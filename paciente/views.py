from django.shortcuts import render, redirect
from medico.models import DadosMedico, Especialidades, DatasAbertas, is_medico
from django.http import HttpResponse
from datetime import datetime
from .models import Consulte, Documento
from django.contrib import messages
from django.contrib.messages import constants
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def home(request):
    if request.method == 'GET':
        medico_filtrar = request.GET.get('medico')
        especialidades_filtrar = request.GET.getlist('especialidades')        
        medicos = DadosMedico.objects.all()
        if medico_filtrar:
            medicos = medicos.filter(nome__icontains = medico_filtrar)
        
        if especialidades_filtrar:
            medicos = medicos.filter(especialidade_id__in = especialidades_filtrar)
        
        especialidades = Especialidades.objects.all()
        return render(request, 'home.html', {'medicos':medicos, 'especialidades':especialidades, 'is_medico': is_medico(request.user)})

@login_required
def escolher_horario(request, id_dados_medicos):
    if request.method == 'GET':
        medico = DadosMedico.objects.get(id = id_dados_medicos)
        datas_abertas = DatasAbertas.objects.filter(user = medico.user).filter(data__gte = datetime.now()).filter(agendado = False)
        return render(request, 'escolher_horario.html', {'medico':medico, 'datas_abertas':datas_abertas, 'is_medico': is_medico(request.user)})

@login_required
def agendar_horario(request, id_data_aberta):
    if request.method == 'GET':
        data_aberta = DatasAbertas.objects.get(id = id_data_aberta)
        

        horario_agendado = Consulte(
            paciente = request.user,
            data_aberta = data_aberta
        )
        horario_agendado.save()

        data_aberta.agendado = True
        data_aberta.save()

        messages.add_message(request, constants.SUCCESS, 'Horario agendado com sucesso.')
        return redirect('/pacientes/minhas_consultas')    

@login_required
def minhas_consultas(request):
    if request.method == 'GET':
        especialidades = Especialidades.objects.all()
        minhas_consultas = Consulte.objects.filter(paciente = request.user).filter(data_aberta__data__gte=datetime.now())
        data = request.GET.get('data')
        especialidade = request.GET.get('especialidade')
        print(data)
        if data:            
            minhas_consultas = minhas_consultas.filter(data_aberta__data__gte = data)
        
        if especialidade:
            minhas_consultas = minhas_consultas.filter(data_aberta__user__dadosmedico__especialidade__id = especialidade)

        return render(request, 'minhas_consultas.html', {'minhas_consultas':minhas_consultas, 'especialidades': especialidades, 'is_medico': is_medico(request.user)})

@login_required
def consulta(request, id_consulta):
    if request.method == 'GET':
        consulta = Consulte.objects.get(id = id_consulta)        
        if request.user != consulta.paciente:
            messages.add_message(request, constants.ERROR, 'Essa consulta não pertence a esse usuário')
            redirect ('/pacientes/minhas_consultas')
        documentos = Documento.objects.filter(consulta=consulta)
        dado_medico = DadosMedico.objects.get(user = consulta.data_aberta.user)
        return render(request, 'consulta.html', {'consulta': consulta, 'dado_medico': dado_medico, 'documentos': documentos, 'is_medico': is_medico(request.user)})

@login_required
def cancelar_consulta(request, id_consulta):
    consulta = Consulte.objects.get(id = id_consulta)
    if request.user != consulta.paciente:
        messages.add_message(request, constants.ERROR, 'Essa consulta não pertence a esse usuário')
        redirect ('/pacientes/minhas_consultas')
    if consulta.status == 'F':
        messages.add_message(request, constants.ERROR, 'Essa consulta já foi finalizada! Não é possível cancela-la.')
        return redirect(f'/pacientes/minhas_consultas')
    
    consulta.status = 'C'
    consulta.save()
    return redirect(f'/pacientes/minhas_consultas')
