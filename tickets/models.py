from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import os


class Perfil(models.Model):
    TIPO_CHOICES = [
        ('TECNICO', 'Técnico'),
        ('FUNCIONAL', 'Funcional'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='FUNCIONAL')

    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_display()}"

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'


# Signal para criar perfil automaticamente quando um usuário é criado
@receiver(post_save, sender=User)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.get_or_create(user=instance, defaults={'tipo': 'FUNCIONAL'})


@receiver(post_save, sender=User)
def salvar_perfil_usuario(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()


class Chamado(models.Model):
    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('EM_ANDAMENTO', 'Em andamento'),
        ('BLOQUEADO', 'Com Bloqueio'),
        ('VALIDACAO', 'Aguardando Validação'),
        ('MIGRACAO', 'Em migração'),
        ('CONCLUIDO', 'Concluído'),
        ('DOC_PENDENTE', 'Documentação Pendente'),
    ]

    CATEGORIA_CHOICES = [
        ('BUG', 'Bug / Erro'),
        ('NOVA_IMPLEMENTACAO', 'Nova Implementação'),
        ('ALTERACAO', 'Alteração'),
        ('REFATORACAO', 'Refatoração'),
        ('DEVOPS', 'DevOps / Infra'),
    ]

    PRIORIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]

    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTO')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='MEDIA')

    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chamados_solicitados')
    tecnico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='chamados_atribuidos')

    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.id} - {self.titulo}"

    class Meta:
        ordering = ['-data_criacao']
        verbose_name = 'Chamado'
        verbose_name_plural = 'Chamados'


class HistoricoChamado(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name='historico')
    descricao = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Histórico #{self.chamado.id} - {self.data.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        ordering = ['data']


# NOVO MODELO: Anexo
def upload_anexo_path(instance, filename):
    """Define o caminho de upload: anexos/chamado_{id}/{filename}"""
    return f'anexos/chamado_{instance.chamado.id}/{filename}'


class AnexoChamado(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name='anexos')
    arquivo = models.FileField(upload_to=upload_anexo_path)
    nome_original = models.CharField(max_length=255)
    tamanho = models.IntegerField(help_text='Tamanho em bytes')
    data_upload = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Anexo: {self.nome_original} - Chamado #{self.chamado.id}"

    def get_tamanho_formatado(self):
        """Retorna o tamanho formatado (KB, MB, etc)"""
        tamanho = self.tamanho
        for unidade in ['bytes', 'KB', 'MB', 'GB']:
            if tamanho < 1024.0:
                return f"{tamanho:.1f} {unidade}"
            tamanho /= 1024.0
        return f"{tamanho:.1f} TB"

    class Meta:
        ordering = ['data_upload']
        verbose_name = 'Anexo do Chamado'
        verbose_name_plural = 'Anexos dos Chamados'