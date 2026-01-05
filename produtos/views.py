from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Produto, Pedido, ItemPedido, Avaliacao, Cupom
from django.contrib.auth.decorators import login_required
from django.conf import settings
import stripe 
from django.urls import reverse
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Avg #importante para calcular medias
from .forms import AvaliacaoForm


stripe.api_key = settings.STRIPE_SECRET_KEY


def home(request):
    # 1. Buscar todos os produtos ordenados (a ordem é importante para a paginação não se perder)
    produtos_list = Produto.objects.all().order_by('id')
    
    # 2. Configurar o Paginator
    # Vamos mostrar 4 produtos por página para testares já (depois podes mudar para 8 ou 12)
    paginator = Paginator(produtos_list, 20)
    # 3. Pegar o número da página da URL (ex: site.com/?page=2)
    page_number = request.GET.get('page')
    
    # 4. Obter apenas os produtos daquela página
    produtos_paginados = paginator.get_page(page_number)
    
    return render(request, 'home.html', {'produtos': produtos_paginados})

########### DETALHE PRODUTO #####################

def detalhe_produto(request, id):
    produto = get_object_or_404(Produto, id=id)
    
    # 1. Processar o formulário de nova avaliação
    if request.method == 'POST' and request.user.is_authenticated:
        form = AvaliacaoForm(request.POST)
        if form.is_valid():
            nova_avaliacao = form.save(commit=False)
            nova_avaliacao.produto = produto
            nova_avaliacao.usuario = request.user
            nova_avaliacao.save()
            messages.success(request, 'Obrigado pela tua avaliação!')
            return redirect('detalhe_produto', id=id)
    else:
        form = AvaliacaoForm()

    # 2. Buscar avaliações existentes
    avaliacoes = produto.avaliacoes.all().order_by('-data_criacao')
    
    # 3. Calcular Média (ex: 4.5)
    media_estrelas = avaliacoes.aggregate(Avg('estrelas'))['estrelas__avg'] or 0

    return render(request, 'detalhe_produto.html', {
        'produto': produto,
        'avaliacoes': avaliacoes,
        'media_estrelas': round(media_estrelas, 1), # Arredonda para 1 casa decimal
        'form': form
    })
####################

@login_required(login_url='login')
def adicionar_ao_carrinho(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    carrinho = request.session.get('carrinho', {})
    produto_id_str = str(produto_id)
    
    # Quantidade que já está no carrinho (se não tiver, é 0)
    qtd_no_carrinho = carrinho.get(produto_id_str, {}).get('quantidade', 0)
    
    # VERIFICAÇÃO DE STOCK
    if (qtd_no_carrinho + 1) > produto.stock:
        messages.warning(request, f'Desculpe, só temos {produto.stock} unidades de {produto.nome} em stock.')
        return redirect('detalhe_produto', id=produto_id)

    # Se passou no teste, adiciona
    if produto_id_str in carrinho:
        carrinho[produto_id_str]['quantidade'] += 1
    else:
        carrinho[produto_id_str] = {
            'quantidade': 1,
            'preco': str(produto.preco)
        }
        
    request.session['carrinho'] = carrinho
    messages.success(request, f'O produto "{produto.nome}" foi adicionado ao carrinho!')
    return redirect('detalhe_produto', id=produto_id)

@login_required(login_url='login')
def ver_carrinho(request):
    """Mostra os itens do carrinho."""
    carrinho = request.session.get('carrinho', {})
    itens_do_carrinho = []
    total_geral = 0
    
    for id_str, dados in carrinho.items():
        produto = get_object_or_404(Produto, id=int(id_str))
        preco_item = float(dados['preco'])
        quantidade = dados['quantidade']
        subtotal = preco_item * quantidade
        total_geral += subtotal
        
        itens_do_carrinho.append({
            'produto': produto,
            'quantidade': quantidade,
            'subtotal': subtotal,
        })
        
    contexto = {
        'itens_do_carrinho': itens_do_carrinho,
        'total_geral': total_geral,
    }
    
    return render(request, 'carrinho.html', contexto)


def remover_do_carrinho(request, produto_id):
    """Remove um item do carrinho."""
    carrinho = request.session.get('carrinho', {})
    produto_id_str = str(produto_id)
    
    if produto_id_str in carrinho:
        del carrinho[produto_id_str]
        request.session.modified = True # É necessário para que o Django perceba a mudança
        
    return redirect('ver_carrinho')


def atualizar_quantidade_carrinho(request, produto_id):
    carrinho = request.session.get('carrinho', {})
    produto_id_str = str(produto_id)
    produto = get_object_or_404(Produto, id=produto_id) # Buscar produto para ver stock real

    if request.method == 'POST':
        try:
            nova_quantidade = int(request.POST.get('quantidade'))
        except (ValueError, TypeError):
            nova_quantidade = 1 

        if produto_id_str in carrinho:
            if nova_quantidade > 0:
                # VERIFICAÇÃO DE STOCK
                if nova_quantidade > produto.stock:
                    # Se pedir mais do que existe, define para o máximo disponível
                    carrinho[produto_id_str]['quantidade'] = produto.stock
                    messages.warning(request, f'Stock limitado! Ajustámos a quantidade de {produto.nome} para {produto.stock} (máximo disponível).')
                else:
                    # Se tiver stock suficiente, tudo bem
                    carrinho[produto_id_str]['quantidade'] = nova_quantidade
            else:
                del carrinho[produto_id_str]
            
            request.session.modified = True
            
    return redirect('ver_carrinho')

####################### CHECKOUT ##################

@login_required(login_url='login')
def checkout(request):
    carrinho = request.session.get('carrinho', {})
    if not carrinho:
        return redirect('ver_carrinho')

    # 1. Calcula Subtotal
    subtotal = 0
    for item in carrinho.values():
        subtotal += float(item['preco']) * item['quantidade']

    # 2. Verifica Cupão
    cupom_id = request.session.get('cupom_id')
    desconto_valor = 0
    cupom_codigo = None

    if cupom_id:
        try:
            cupom = Cupom.objects.get(id=cupom_id, ativo=True)
            desconto_valor = subtotal * (cupom.desconto / 100)
            cupom_codigo = cupom.codigo
        except Cupom.DoesNotExist:
            request.session['cupom_id'] = None

    # 3. Calcula Finais
    CUSTO_ENVIO = 5.00
    total_com_desconto = subtotal - desconto_valor
    total_final = total_com_desconto + CUSTO_ENVIO

    # Guarda na sessão para o pagamento usar depois
    request.session['checkout_dados'] = {
        'subtotal': subtotal,
        'desconto': desconto_valor, # Guardamos quanto foi descontado
        'custo_envio': CUSTO_ENVIO,
        'total_final': total_final
    }

    return render(request, 'checkout.html', {
        'subtotal': subtotal,
        'desconto': desconto_valor, # Passamos para o HTML
        'cupom_codigo': cupom_codigo, # Passamos para o HTML
        'custo_envio': CUSTO_ENVIO,
        'total_final': total_final
    })

@login_required(login_url='login')
def processar_checkout(request):
    """Recebe o formulário e manda para o Stripe."""
    if request.method == 'POST':
        # 1. Guardar os dados de envio na sessão (Temporariamente)
        #    Só vamos gravar no banco DEPOIS do pagamento ser sucesso.
        request.session['dados_envio_cliente'] = {
            'endereco': request.POST.get('endereco'),
            'cidade': request.POST.get('cidade'),
            'codigo_postal': request.POST.get('codigo_postal'),
            'telemovel': request.POST.get('telemovel'),
        }
        
        # 2. Seguir para o pagamento Stripe
        return redirect('criar_pagamento')
    
    return redirect('checkout')

############# PAGAMENTO #################

@login_required(login_url='login')
def criar_pagamento(request):
    carrinho = request.session.get('carrinho', {})
    checkout_dados = request.session.get('checkout_dados', {})
    
    if not carrinho or not checkout_dados:
        return redirect('ver_carrinho')

    itens_stripe = []
    
    # 1. VERIFICAÇÃO FINAL DE STOCK (Gatekeeper)
    for id_str, dados in carrinho.items():
        produto = get_object_or_404(Produto, id=int(id_str))
        qtd_solicitada = dados['quantidade']
        
        # Se entretanto o stock acabou ou diminuiu na base de dados
        if qtd_solicitada > produto.stock:
            messages.error(request, f'Atenção: O produto {produto.nome} acabou de esgotar ou tem stock insuficiente. Por favor atualize o carrinho.')
            return redirect('ver_carrinho')

        # Se passou na verificação, adiciona ao Stripe
        itens_stripe.append({
            'price_data': {
                'currency': 'eur',
                'unit_amount': int(float(dados['preco']) * 100),
                'product_data': {'name': produto.nome},
            },
            'quantity': qtd_solicitada,
        })

    # Portes
    custo_envio = checkout_dados.get('custo_envio', 0)
    if custo_envio > 0:
        itens_stripe.append({
            'price_data': {
                'currency': 'eur',
                'unit_amount': int(custo_envio * 100),
                'product_data': {'name': 'Portes de Envio e Processamento'},
            },
            'quantity': 1,
        })

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card','mb_way','paypal','klarna'],
            line_items=itens_stripe,
            mode='payment',
            success_url=request.build_absolute_uri(reverse('pagamento_sucesso')),
            cancel_url=request.build_absolute_uri(reverse('pagamento_cancelar')),
        )
        return redirect(session.url, code=303)
    except Exception as e:
        messages.error(request, f'Erro no pagamento: {e}')
        return redirect('ver_carrinho')


# ----------------------------------------------------------------------
# Funções de Redirecionamento Pós-Pagamento

@login_required(login_url='login')
def pagamento_sucesso(request):
    carrinho = request.session.get('carrinho', {})
    checkout_dados = request.session.get('checkout_dados', {})
    dados_cliente = request.session.get('dados_envio_cliente', {}) # Recupera a morada

    if not carrinho:
        return redirect('home')

    # Criar o Pedido com os dados novos
    novo_pedido = Pedido.objects.create(
        usuario=request.user,
        total_pago=checkout_dados.get('total_final', 0),
        custo_envio=checkout_dados.get('custo_envio', 0),
        status='Pago',
        
        # Dados de Envio
        endereco=dados_cliente.get('endereco', ''),
        cidade=dados_cliente.get('cidade', ''),
        codigo_postal=dados_cliente.get('codigo_postal', ''),
        telemovel=dados_cliente.get('telemovel', '')
    )
    for id_str, dados in carrinho.items():
        produto = get_object_or_404(Produto, id=int(id_str))
        # --- NOVO CÓDIGO AQUI ---
        # 1. Verifica se tem stock suficiente (segurança extra)
        if produto.stock >= dados['quantidade']:
            produto.stock -= dados['quantidade'] # Subtrai a quantidade comprada
            produto.save() # Guarda o novo stock na base de dados
        else:
            # Opcional: Aqui poderiamos lidar com o erro, mas como já validámos antes,
            # vamos apenas colocar o stock a 0 para não ficar negativo.
            produto.stock = 0
            produto.save()
        # ------------------------

    lista_itens_email = [] # Vamos criar uma lista para meter no texto do email
    # ... (O resto do código que cria os ItensPedido mantém-se igual) ...
    for id_str, dados in carrinho.items():
        produto = get_object_or_404(Produto, id=int(id_str))
        ItemPedido.objects.create(
            pedido=novo_pedido,
            produto=produto,
            preco=dados['preco'],
            quantidade=dados['quantidade']
        )
        # Adiciona à lista de texto para o email
        lista_itens_email.append(f"- {dados['quantidade']}x {produto.nome} (€ {dados['preco']})")
    # -------------------------------------------------------
    # 3. ENVIAR EMAIL DE CONFIRMAÇÃO (NOVO BLOCO!)
    # -------------------------------------------------------
    try:
        assunto = f'Confirmação do Pedido #{novo_pedido.id} - Loja Teste'
        
        # Criação da mensagem de texto simples
        itens_texto = "\n".join(lista_itens_email)
        mensagem = f"""
        Olá {request.user.username},
        
        Obrigado pela tua compra na Loja Teste!
        O teu pedido #{novo_pedido.id} foi recebido e já está a ser processado.
        
        RESUMO DO PEDIDO:
        {itens_texto}
        
        -----------------------------------
        Morada de Envio: {novo_pedido.endereco}, {novo_pedido.cidade}
        Total Pago: € {novo_pedido.total_pago}
        -----------------------------------
        
        Enviaremos outro email quando a encomenda for enviada.
        
        Cumprimentos,
        Equipa Loja teste
        """
        
        send_mail(
            assunto,
            mensagem,
            settings.EMAIL_HOST_USER, # Remetente
            [request.user.email],     # Destinatário (email do cliente logado)
            fail_silently=False,
        )
        # --- NOVO: EMAIL PARA O ADMIN (TU) ---
        assunto_admin = f'💰 Nova Venda! Pedido #{novo_pedido.id} (€ {novo_pedido.total_pago})'
        
        mensagem_admin = f"""
        Boas notícias! Acabaste de receber uma nova encomenda no site.
        
        DADOS DO CLIENTE:
        Nome: {request.user.username}
        Email: {request.user.email}
        Telemóvel: {novo_pedido.telemovel}
        
        ITENS VENDIDOS:
        {itens_texto}
        
        MORADA DE ENVIO:
        {novo_pedido.endereco}
        {novo_pedido.codigo_postal} {novo_pedido.cidade}
        
        Total da Fatura: € {novo_pedido.total_pago}
        
        Vai ao painel de admin para processar: http://127.0.0.1:8000/admin/
        """
        
        # ATENÇÃO: Coloca aqui o TEU email onde queres receber o alerta
        meu_email_admin = 'wilson.goncalves07@gmail.com' 
        
        send_mail(assunto_admin, mensagem_admin, settings.EMAIL_HOST_USER, [meu_email_admin], fail_silently=False)
    except Exception as e:
        # Se o email falhar, não queremos que o site crash. Apenas imprimimos o erro.
        print(f"Erro ao enviar email: {e}")

    # -------------------------------------------------------

    # Limpar sessões
    request.session.pop('carrinho', None)
    request.session.pop('checkout_dados', None)
    request.session.pop('dados_envio_cliente', None)
    request.session.pop('cupom_id', None) 

    return render(request, 'status.html', {'status': 'sucesso', 'pedido': novo_pedido})

@login_required(login_url='login')
def pagamento_cancelar(request):
    """O utilizador cancelou ou fechou a janela."""
    messages.error(request, 'O pagamento foi cancelado. Por favor, tente novamente.')
    return redirect('ver_carrinho')

############# Acompanhamento de encomendas ##################

@login_required(login_url='login')
def minhas_encomendas(request):
    """Lista as encomendas do utilizador logado."""
    # Busca os pedidos do utilizador, ordenados do mais recente para o mais antigo
    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-data_pedido')
    
    return render(request, 'minhas_encomendas.html', {'pedidos': pedidos})


def pesquisa(request):
    """Pesquisa produtos pelo nome."""
    query = request.GET.get('q') # Pega o termo que o utilizador escreveu
    
    if query:
        # __icontains significa: "Contém este texto" e "Ignora maiúsculas/minúsculas"
        produtos = Produto.objects.filter(nome__icontains=query)
    else:
        # Se pesquisou vazio, não mostra nada ou redireciona
        produtos = []

    return render(request, 'pesquisa.html', {'produtos': produtos, 'query': query})

def aplicar_cupom(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        try:
            cupom = Cupom.objects.get(codigo=codigo, ativo=True)
            # Guarda o ID do cupão na sessão do navegador
            request.session['cupom_id'] = cupom.id
            messages.success(request, f'Cupão "{codigo}" aplicado! {cupom.desconto}% de desconto.')
        except Cupom.DoesNotExist:
            request.session['cupom_id'] = None
            messages.error(request, 'Cupão inválido ou expirado.')
            
    return redirect('checkout')