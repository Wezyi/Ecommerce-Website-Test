from django.contrib import admin
from .models import Produto, Pedido, ItemPedido, Cupom, Avaliacao

class StockFilter(admin.SimpleListFilter):
    title = 'Estado do Stock' # Título que aparece na barra lateral
    parameter_name = 'stock_status'

    def lookups(self, request, model_admin):
        # As opções que vão aparecer no filtro
        return (
            ('esgotado', 'Esgotado (0)'),
            ('com_stock', 'Com Stock (>0)'),
        )

    def queryset(self, request, queryset):
        # A lógica de filtragem
        if self.value() == 'esgotado':
            return queryset.filter(stock=0)
        if self.value() == 'com_stock':
            return queryset.filter(stock__gt=0)
        return queryset

# 2. ATUALIZAR O ADMIN DO PRODUTO
@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    # Colunas que aparecem na tabela
    list_display = ('nome', 'preco', 'stock', 'status_stock') 
    
    # Adiciona a barra de filtros à direita
    list_filter = (StockFilter, 'preco') 
    
    # Permite pesquisar pelo nome
    search_fields = ('nome',)
    
    # MAGIA: Permite editar o stock diretamente na lista sem entrar no produto!
    list_editable = ('stock', 'preco') 
    
    # Pequena função para mostrar um ícone visual (Opcional, mas fica bonito)
    def status_stock(self, obj):
        if obj.stock == 0:
            return '🔴 Esgotado'
        elif obj.stock < 5:
            return '🟠 Baixo'
        return '🟢 OK'
    status_stock.short_description = 'Estado'



# 2. Configuração dos Itens (Para aparecerem DENTRO do Pedido)
class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0  # Não mostra linhas vazias extra
    readonly_fields = ('produto', 'preco', 'quantidade') # Para não alterares o histórico por engano
    can_delete = False # Evita apagar itens de encomendas já feitas

# 3. Configuração do Pedido Principal
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # O que aparece na lista geral
    list_display = ('id', 'usuario', 'data_pedido', 'total_pago', 'status', 'cidade')
    
    # Filtros na barra lateral (Útil para filtrar por 'Pago' ou 'Enviado')
    list_filter = ('status', 'data_pedido')
    
    # Barra de pesquisa (Podes pesquisar por nome do cliente ou ID)
    search_fields = ('id', 'usuario__username', 'endereco', 'stripe_id')
    
    # Aqui ligamos os itens ao pedido
    inlines = [ItemPedidoInline]
    
    # Campos que não devem ser editados
    readonly_fields = ('id','data_pedido', 'usuario', 'total_pago', 'custo_envio', 'stripe_id')
    
    # Organização dos campos na tela de edição
    fieldsets = (
        ('Dados do Pedido', {
            'fields': ('id', 'status', 'data_pedido', 'stripe_id')
        }),
        ('Cliente', {
            'fields': ('usuario', 'telemovel')
        }),
        ('Morada de Envio', {
            'fields': ('endereco', 'cidade', 'codigo_postal')
        }),
        ('Valores', {
            'fields': ('custo_envio', 'total_pago')
        }),
    )
@admin.register(Cupom)
class CupomAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'desconto', 'ativo') # Mostra estas colunas na lista
    search_fields = ('codigo',) # Permite pesquisar pelo código

@admin.register(Avaliacao) # Se não tiveres importado Avaliacao no topo, importa!
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'produto', 'estrelas', 'data_criacao')