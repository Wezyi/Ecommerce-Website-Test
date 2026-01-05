from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    imagem = models.ImageField(upload_to='produtos/', null=True, blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    tamanho = models.DecimalField(max_digits=10,decimal_places=0, null=True, blank=True)
    descricao = models.TextField(blank=True)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return self.nome


class Offer(models.Model):
    code = models.CharField(max_length=7)
    description = models.CharField(max_length=240)
    discount = models.FloatField()


class Pedido(models.Model):
    STATUS_CHOICES = (
        ('Pago', 'Pago'),
        ('Em tratamento', 'Em tratamento'),
        ('Enviado', 'Enviado'),
        ('Entregue', 'Entregue'),
        ('Cancelado', 'Cancelado'),
    )

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    data_pedido = models.DateTimeField(auto_now_add=True)
    total_pago = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pago')
    
    # Campos de Envio
    endereco = models.CharField(max_length=255, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    codigo_postal = models.CharField(max_length=20, blank=True)
    telemovel = models.CharField(max_length=20, blank=True)
    custo_envio = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    stripe_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-data_pedido']

    def __str__(self):
        return f'Pedido #{self.id} de {self.usuario.username}'

    # --- LÓGICA NOVA DE EMAIL ---

    def enviar_email_enviado(self):
        """Envia email quando o status muda para Enviado."""
        assunto = f'A tua encomenda #{self.id} foi enviada! 🚚'
        mensagem = f"""
        Olá {self.usuario.username},
        
        Boas notícias! A tua encomenda #{self.id} acabou de sair do nosso armazém.
        
        Ela está a caminho de:
        {self.endereco}
        {self.codigo_postal} {self.cidade}
        
        Obrigado por comprares na Loja Teste!
        """
        
        try:
            send_mail(
                assunto,
                mensagem,
                settings.EMAIL_HOST_USER,
                [self.usuario.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Erro ao enviar email de envio: {e}")

    def save(self, *args, **kwargs):
        # Verifica se é uma edição (self.pk existe) e não uma criação nova
        if self.pk:
            # Vamos buscar o pedido como ele está AGORA na base de dados (antes de guardar a mudança)
            antigo = Pedido.objects.get(pk=self.pk)
            
            # Se o status antigo NÃO era 'Enviado' e o novo É 'Enviado'
            if antigo.status != 'Enviado' and self.status == 'Enviado':
                self.enviar_email_enviado()

        # Continua o processo normal de guardar
        super().save(*args, **kwargs)

class ItemPedido(models.Model):
    """Itens específicos dentro de uma Encomenda."""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey('Produto', on_delete=models.SET_NULL, null=True) # Mantém o produto original
    preco = models.DecimalField(max_digits=10, decimal_places=2) # Preço na hora da compra
    quantidade = models.IntegerField(default=1)

    def get_subtotal(self):
        return self.preco * self.quantidade

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        return f'{self.quantidade}x {self.produto.nome} (Pedido {self.pedido.id})'

class Cupom(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    desconto = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Percentagem de desconto (0 a 100)'
    )
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.codigo
    
    
class Avaliacao(models.Model):
    produto = models.ForeignKey(Produto, related_name='avaliacoes', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    comentario = models.TextField(max_length=500, blank=True)
    estrelas = models.IntegerField(default=5, choices=[(i, str(i)) for i in range(1, 6)]) # 1 a 5
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.usuario.username} - {self.produto.nome}'
