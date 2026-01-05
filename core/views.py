from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings

def sobre(request):
    return render(request, 'core/sobre.html')

def politica_privacidade(request):
    return render(request, 'core/privacidade.html')

def termos_condicoes(request):
    return render(request, 'core/termos.html')

def contacto(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email_cliente = request.POST.get('email')
        assunto = request.POST.get('assunto')
        mensagem = request.POST.get('mensagem')
        
        # Monta o email que TU vais receber
        msg_final = f"""
        Recebeste uma nova mensagem pelo site:
        
        Nome: {nome}
        Email: {email_cliente}
        Assunto: {assunto}
        
        Mensagem:
        {mensagem}
        """
        
        try:
            # Envia email para o ADMIN (TU)
            send_mail(
                f'Contato Site: {assunto}',
                msg_final,
                settings.EMAIL_HOST_USER, # Remetente (o teu gmail)
                [settings.EMAIL_HOST_USER], # Destinatário (tu mesmo)
                fail_silently=False,
            )
            messages.success(request, 'Mensagem enviada com sucesso! Responderemos em breve.')
            return redirect('contacto')
        except Exception as e:
            messages.error(request, 'Erro ao enviar mensagem. Tente novamente.')
            
    return render(request, 'core/contacto.html')
