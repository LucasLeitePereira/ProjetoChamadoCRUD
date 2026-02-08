from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import CadastroForm, ChamadoForm
from django.contrib import messages
from .models import Perfil, Chamado, HistoricoChamado, AnexoChamado
import os


def cadastro_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('password')
        confirmar = request.POST.get('confirm_password')
        tipo_conta = request.POST.get('tipo')  # 'FUNCIONAL' ou 'TECNICO'

        # Validação de senha
        if senha != confirmar:
            messages.error(request, "As senhas não coincidem.")
            return render(request, 'tickets/auth/cadastro.html')

        # Verifica se usuário já existe
        if User.objects.filter(username=usuario).exists():
            messages.error(request, "Este usuário já está em uso.")
            return render(request, 'tickets/auth/cadastro.html')

        # Verifica se email já existe
        if User.objects.filter(email=email).exists():
            messages.error(request, "Este e-mail já está em uso.")
            return render(request, 'tickets/auth/cadastro.html')

        # Validação do tipo
        if tipo_conta not in ['FUNCIONAL', 'TECNICO']:
            messages.error(request, "Tipo de conta inválido.")
            return render(request, 'tickets/auth/cadastro.html')

        try:
            # 1. Cria o usuário (o signal criará o perfil automaticamente)
            novo_user = User.objects.create_user(
                username=usuario,
                email=email,
                password=senha
            )

            # 2. Atualiza o tipo do perfil que foi criado automaticamente
            novo_user.perfil.tipo = tipo_conta
            novo_user.perfil.save()

            # Debug
            print(f"Usuário criado: {novo_user.username}")
            print(f"Perfil atualizado: {novo_user.perfil.tipo}")

            # 3. Fazer login automático
            login(request, novo_user)

            # 4. Mensagem de boas-vindas e redirecionar
            messages.success(request,
                             f"Bem-vindo(a), {novo_user.username}! Sua conta {novo_user.perfil.get_tipo_display()} foi criada com sucesso.")
            return redirect('dashboard')

        except Exception as e:
            messages.error(request, f"Erro ao criar conta: {str(e)}")
            print(f"Erro detalhado: {e}")
            return render(request, 'tickets/auth/cadastro.html')

    return render(request, 'tickets/auth/cadastro.html')

def login_view(request):
    # Se o usuário já está logado, redireciona para o dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bem-vindo de volta, {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Usuário ou senha inválidos.")
    else:
        form = AuthenticationForm()

    return render(request, 'tickets/auth/index.html', {'form': form})

@login_required
def dashboard_view(request):
    # Verifica se o usuário tem perfil
    try:
        perfil = request.user.perfil
    except Perfil.DoesNotExist:
        messages.error(request, "Seu usuário não possui um perfil válido. Contate o administrador.")
        logout(request)
        return redirect('login')

    if perfil.tipo == 'TECNICO':
        chamados = Chamado.objects.all()
    else:
        chamados = Chamado.objects.filter(solicitante=request.user)

    # Aplicar filtros
    search = request.GET.get('search')
    if search:
        chamados = chamados.filter(titulo__icontains=search)

    status = request.GET.get('status')
    if status:
        chamados = chamados.filter(status=status)

    prioridade = request.GET.get('prioridade')
    if prioridade:
        chamados = chamados.filter(prioridade=prioridade)

    # Filtro por solicitante (funcional)
    solicitante_id = request.GET.get('solicitante')
    if solicitante_id:
        chamados = chamados.filter(solicitante_id=solicitante_id)

    # Filtro por técnico
    tecnico_id = request.GET.get('tecnico')
    if tecnico_id:
        if tecnico_id == 'nao_atribuido':
            chamados = chamados.filter(tecnico__isnull=True)
        else:
            chamados = chamados.filter(tecnico_id=tecnico_id)

    chamados = chamados.order_by('-data_criacao')

    # Buscar lista de funcionais e técnicos para os dropdowns
    funcionais = User.objects.filter(perfil__tipo='FUNCIONAL').order_by('username')
    tecnicos = User.objects.filter(perfil__tipo='TECNICO').order_by('username')

    return render(request, 'tickets/dashboard.html', {
        'chamados': chamados,
        'funcionais': funcionais,
        'tecnicos': tecnicos
    })

@login_required
def criar_view(request):
    if request.method == 'POST':
        form = ChamadoForm(request.POST)
        if form.is_valid():
            chamado = form.save(commit=False)
            chamado.solicitante = request.user
            chamado.status = 'ABERTO'
            chamado.save()

            # Processar anexos
            anexos = request.FILES.getlist('anexos')
            for arquivo in anexos:
                AnexoChamado.objects.create(
                    chamado=chamado,
                    arquivo=arquivo,
                    nome_original=arquivo.name,
                    tamanho=arquivo.size,
                    usuario=request.user
                )

            # Criar histórico inicial
            mensagem_historico = f"Chamado criado por {request.user.username}"
            if anexos:
                mensagem_historico += f" com {len(anexos)} anexo(s)"

            HistoricoChamado.objects.create(
                chamado=chamado,
                descricao=mensagem_historico,
                usuario=request.user
            )

            messages.success(request, 'Chamado criado com sucesso!')
            return redirect('dashboard')
    else:
        form = ChamadoForm()

    return render(request, 'tickets/criar.html', {'form': form})

@login_required
def detalhes_view(request, id):
    chamado = get_object_or_404(Chamado, id=id)

    # Segurança
    if request.user.perfil.tipo != 'TECNICO' and chamado.solicitante != request.user:
        messages.error(request, 'Você não tem permissão para acessar este chamado.')
        return redirect('dashboard')

    if request.method == 'POST':
        # Processar novos anexos
        novos_anexos = request.FILES.getlist('novos_anexos')
        if novos_anexos:
            for arquivo in novos_anexos:
                AnexoChamado.objects.create(
                    chamado=chamado,
                    arquivo=arquivo,
                    nome_original=arquivo.name,
                    tamanho=arquivo.size,
                    usuario=request.user
                )
            HistoricoChamado.objects.create(
                chamado=chamado,
                descricao=f"{request.user.username} adicionou {len(novos_anexos)} anexo(s)",
                usuario=request.user
            )

        # Atualizar campos básicos (apenas se for ABERTO)
        if chamado.status == 'ABERTO' and (
                request.user.perfil.tipo == 'TECNICO' or chamado.solicitante == request.user):
            chamado.titulo = request.POST.get('titulo', chamado.titulo)
            chamado.descricao = request.POST.get('descricao', chamado.descricao)
            chamado.categoria = request.POST.get('categoria', chamado.categoria)
            chamado.prioridade = request.POST.get('prioridade', chamado.prioridade)

        # Apenas técnicos podem alterar status e técnico
        if request.user.perfil.tipo == 'TECNICO':
            novo_status = request.POST.get('status')
            novo_tecnico_id = request.POST.get('tecnico')

            # Registrar mudança de status
            if novo_status and novo_status != chamado.status:
                status_antigo = chamado.get_status_display()
                chamado.status = novo_status
                status_novo = chamado.get_status_display()

                HistoricoChamado.objects.create(
                    chamado=chamado,
                    descricao=f"Status alterado de '{status_antigo}' para '{status_novo}'",
                    usuario=request.user
                )

            # Registrar mudança de técnico
            tecnico_antigo_id = chamado.tecnico.id if chamado.tecnico else None
            if novo_tecnico_id != str(tecnico_antigo_id if tecnico_antigo_id else ''):
                if novo_tecnico_id:
                    tecnico_obj = User.objects.get(id=novo_tecnico_id)
                    HistoricoChamado.objects.create(
                        chamado=chamado,
                        descricao=f"Técnico atribuído: {tecnico_obj.username}",
                        usuario=request.user
                    )
                    chamado.tecnico = tecnico_obj
                else:
                    HistoricoChamado.objects.create(
                        chamado=chamado,
                        descricao="Técnico removido",
                        usuario=request.user
                    )
                    chamado.tecnico = None

        chamado.save()
        messages.success(request, 'Chamado atualizado com sucesso!')
        return redirect('detalhes', id=chamado.id)

    # Buscar técnicos para o dropdown
    tecnicos = User.objects.filter(perfil__tipo='TECNICO')

    return render(request, 'tickets/detalhes.html', {
        'chamado': chamado,
        'tecnicos': tecnicos
    })

@login_required
def deletar_anexo(request, chamado_id, anexo_id):
    """
    View para deletar um anexo do chamado.
    Apenas técnicos ou o próprio usuário que enviou o anexo podem deletá-lo.
    """
    if request.method == 'POST':
        anexo = get_object_or_404(AnexoChamado, id=anexo_id, chamado_id=chamado_id)
        chamado = anexo.chamado

        # Verificar permissões
        if request.user.perfil.tipo == 'TECNICO' or anexo.usuario == request.user:
            # Guardar informações antes de deletar
            nome_arquivo = anexo.nome_original
            caminho_arquivo = anexo.arquivo.path

            # Deletar o arquivo físico do disco
            try:
                if os.path.exists(caminho_arquivo):
                    os.remove(caminho_arquivo)
            except Exception as e:
                messages.warning(request, f'Anexo removido do sistema, mas arquivo físico não pode ser deletado: {e}')

            # Deletar o registro do banco de dados
            anexo.delete()

            # Registrar no histórico
            HistoricoChamado.objects.create(
                chamado=chamado,
                usuario=request.user,
                descricao=f'Anexo "{nome_arquivo}" foi deletado por {request.user.username}'
            )

            messages.success(request, f'Anexo "{nome_arquivo}" deletado com sucesso!')
        else:
            messages.error(request, 'Você não tem permissão para deletar este anexo.')

    return redirect('detalhes', id=chamado_id)

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')