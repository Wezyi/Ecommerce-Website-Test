from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegistroUsuarioForm, EditarPerfilForm
from django.contrib.auth.decorators import login_required


def registo(request):
    if request.method == 'POST':
        # Usa o Teu Formulário Personalizado aqui
        form = RegistroUsuarioForm(request.POST) 
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Conta criada para {username}! Faça login agora.')
            return redirect('login')
    else:
        # E aqui também
        form = RegistroUsuarioForm() 
    
    return render(request, 'contas/registo.html', {'form': form})

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        # Carrega o formulário com os dados enviados (POST) E diz quem é o utilizador (instance)
        form = EditarPerfilForm(request.POST, instance=request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'O teu perfil foi atualizado com sucesso!')
            return redirect('editar_perfil') # Recarrega a mesma página
    else:
        # Se for GET (abrir a página), carrega o formulário preenchido com os dados atuais
        form = EditarPerfilForm(instance=request.user)
    
    return render(request, 'contas/editar_perfil.html', {'form': form})