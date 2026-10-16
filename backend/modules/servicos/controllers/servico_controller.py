from flask import jsonify, request
from flask_login import current_user, login_required

from decorators import apenas_tecnico
from exceptions import DominioError
from modules.atendimentos.services.avaliar_service import AvaliarService
from modules.atendimentos.services.listar_avaliacoes_service import ListarAvaliacoesService
from modules.atendimentos.services.listar_orcamentos_service import ListarOrcamentosService
from modules.servicos.services.ampliar_busca_tecnicos_service import AmpliarBuscaTecnicosService
from modules.servicos.services.atribuir_tecnico_service import AtribuirTecnicoService
from modules.servicos.services.aumentar_teto_servico_service import AumentarTetoServicoService
from modules.servicos.services.atualizar_status_servico_service import AtualizarStatusServicoService
from modules.servicos.services.cancelar_servico_service import CancelarServicoService, ExcluirServicoService
from modules.servicos.services.criar_servico_service import CriarServicoService
from modules.servicos.services.acionar_garantia_service import AcionarGarantiaService
from modules.servicos.services.listar_acionamentos_garantia_service import ListarAcionamentosGarantiaService
from modules.servicos.services.listar_aprovacoes_service import ListarAprovacoesService
from modules.servicos.services.listar_meus_servicos_service import ListarMeusServicosService
from modules.servicos.services.obter_historico_aparelho_service import ObterHistoricoAparelhoService
from modules.servicos.services.obter_detalhes_servico_service import ObterDetalhesServicoService
from modules.servicos.services.obter_historico_servico_service import ObterHistoricoServicoService
from modules.servicos.services.registrar_gorjeta_service import RegistrarGorjetaService
from modules.servicos.services.registrar_laudo_service import RegistrarLaudoService
from modules.servicos.services.responder_aprovacao_service import ResponderAprovacaoService
from modules.servicos.services.solicitar_aprovacao_service import SolicitarAprovacaoService
from modules.servicos.services.solicitar_tecnicos_service import SolicitarTecnicosService
from utils import corpo_json


class ServicoController:
    def __init__(self):
        self.criar_servico_service = CriarServicoService()
        self.listar_meus_servicos_service = ListarMeusServicosService()
        self.obter_historico_aparelho_service = ObterHistoricoAparelhoService()
        self.obter_detalhes_servico_service = ObterDetalhesServicoService()
        self.atualizar_status_servico_service = AtualizarStatusServicoService()
        self.obter_historico_servico_service = ObterHistoricoServicoService()
        self.registrar_laudo_service = RegistrarLaudoService()
        self.solicitar_aprovacao_service = SolicitarAprovacaoService()
        self.responder_aprovacao_service = ResponderAprovacaoService()
        self.listar_aprovacoes_service = ListarAprovacoesService()
        self.acionar_garantia_service = AcionarGarantiaService()
        self.listar_acionamentos_garantia_service = ListarAcionamentosGarantiaService()
        self.solicitar_tecnicos_service = SolicitarTecnicosService()
        self.ampliar_busca_tecnicos_service = AmpliarBuscaTecnicosService()
        self.aumentar_teto_servico_service = AumentarTetoServicoService()
        self.registrar_gorjeta_service = RegistrarGorjetaService()
        self.atribuir_tecnico_service = AtribuirTecnicoService()
        self.cancelar_servico_service = CancelarServicoService()
        self.excluir_servico_service = ExcluirServicoService()
        self.listar_orcamentos_service = ListarOrcamentosService()
        self.avaliar_service = AvaliarService()
        self.listar_avaliacoes_service = ListarAvaliacoesService()

    @login_required
    def meus(self):
        status = request.args.get("status")
        # ?como=cliente|tecnico — técnico no modo cliente lista o que abriu;
        # no painel técnico lista o que atende. Sem o parâmetro, usa o role.
        como = (request.args.get("como") or current_user.role or "").strip().lower()
        if como not in {"cliente", "tecnico"}:
            return jsonify({"ok": False, "erro": "Parâmetro 'como' inválido."}), 400
        if como == "tecnico" and not current_user.eh_tecnico:
            return jsonify({"ok": False, "erro": "Acesso negado."}), 403

        servicos = self.listar_meus_servicos_service.executar(current_user.id, como, status)
        return jsonify(servicos)

    @login_required
    def historico_aparelho(self):
        # Sem try/except: DominioError sobe pro errorhandler global (app.py).
        historico = self.obter_historico_aparelho_service.executar(
            current_user,
            request.args.get("equipamento"),
            request.args.get("excluir", type=int),
        )
        return jsonify(historico)

    @login_required
    def criar(self):
        # Aceita JSON ou multipart (com fotos). Qualquer usuário autenticado
        # pode abrir chamado — inclusive quem também é técnico.
        if request.content_type and "multipart/form-data" in request.content_type:
            dados = {
                "tipo_equipamento": (request.form.get("tipo_equipamento") or "").strip(),
                "categoria": (request.form.get("categoria") or "").strip(),
                "equipamento": (request.form.get("equipamento") or "").strip(),
                "titulo": (request.form.get("titulo") or "").strip(),
                "descricao": (request.form.get("descricao") or "").strip(),
                "preco_estimado": request.form.get("preco_estimado") or 0,
                "garantia": request.form.get("garantia"),
                "urgente": request.form.get("urgente"),
                "modalidade": (request.form.get("modalidade") or "").strip(),
                "latitude": request.form.get("latitude"),
                "longitude": request.form.get("longitude"),
            }
            fotos = [f for f in request.files.getlist("fotos") if f and f.filename]
        else:
            dados = corpo_json()
            fotos = []

        try:
            servico, tecnicos_notificados = self.criar_servico_service.executar(dados, current_user, fotos)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({
            "ok": True,
            "servico": servico.to_dict(),
            "tecnicos_notificados": tecnicos_notificados,
        })

    @login_required
    def detalhes(self, servico_id):
        try:
            servico = self.obter_detalhes_servico_service.executar(servico_id)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        payload = servico.to_dict()
        payload["atendimentos"] = [atendimento.to_dict() for atendimento in servico.atendimentos]
        return jsonify(payload)

    @login_required
    def atualizar_status(self, servico_id):
        dados = corpo_json()
        status = dados.get("status")
        if not status:
            return jsonify({"ok": False, "erro": "Status é obrigatório."}), 400

        try:
            servico = self.atualizar_status_servico_service.executar(servico_id, status, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "servico": servico.to_dict()})

    @login_required
    @apenas_tecnico
    def registrar_laudo(self, servico_id):
        # Sem try/except: DominioError sobe e o errorhandler global de app.py
        # devolve a mensagem com o status certo.
        dados = corpo_json()
        servico = self.registrar_laudo_service.executar(servico_id, current_user, dados)
        return jsonify({"ok": True, "servico": servico.to_dict()})

    @login_required
    @apenas_tecnico
    def solicitar_aprovacao(self, servico_id):
        dados = corpo_json()
        aprovacao = self.solicitar_aprovacao_service.executar(servico_id, current_user, dados)
        return jsonify({"ok": True, "aprovacao": aprovacao.to_dict()}), 201

    @login_required
    def responder_aprovacao(self, aprovacao_id):
        dados = corpo_json()
        aprovacao = self.responder_aprovacao_service.executar(aprovacao_id, current_user, dados)
        return jsonify({"ok": True, "aprovacao": aprovacao.to_dict()})

    @login_required
    def aprovacoes(self, servico_id):
        aprovacoes = self.listar_aprovacoes_service.executar(servico_id, current_user)
        return jsonify(aprovacoes)

    @login_required
    def ampliar_busca(self, servico_id):
        resultado = self.ampliar_busca_tecnicos_service.executar(servico_id, current_user)
        return jsonify({"ok": True, **resultado})

    @login_required
    def aumentar_teto(self, servico_id):
        dados = corpo_json()
        servico = self.aumentar_teto_servico_service.executar(
            servico_id, dados.get("valor_maximo_aprovado"), current_user
        )
        return jsonify({"ok": True, "servico": servico.to_dict()})

    @login_required
    def registrar_gorjeta(self, servico_id):
        dados = corpo_json()
        servico = self.registrar_gorjeta_service.executar(servico_id, current_user, dados)
        return jsonify({"ok": True, "servico": servico.to_dict()})

    @login_required
    def acionar_garantia(self, servico_id):
        dados = corpo_json()
        acionamento = self.acionar_garantia_service.executar(servico_id, current_user, dados)
        return jsonify({"ok": True, "acionamento": acionamento.to_dict()}), 201

    @login_required
    def acionamentos_garantia(self, servico_id):
        acionamentos = self.listar_acionamentos_garantia_service.executar(servico_id, current_user)
        return jsonify([acionamento.to_dict() for acionamento in acionamentos])

    @login_required
    def cancelar(self, servico_id):
        try:
            servico = self.cancelar_servico_service.executar(servico_id, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "servico": servico.to_dict()})

    @login_required
    def excluir(self, servico_id):
        try:
            self.excluir_servico_service.executar(servico_id, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "excluido": True})

    @login_required
    def historico(self, servico_id):
        try:
            entradas = self.obter_historico_servico_service.executar(servico_id, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify([entrada.to_dict() for entrada in entradas])

    @login_required
    def orcamentos(self, servico_id):
        try:
            atendimentos = self.listar_orcamentos_service.executar(servico_id, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify(atendimentos)

    @login_required
    def avaliar(self, servico_id):
        dados = corpo_json()
        try:
            avaliacao = self.avaliar_service.executar(servico_id, current_user, dados)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "avaliacao": avaliacao.to_dict()})

    @login_required
    def avaliacoes(self, servico_id):
        try:
            avaliacoes = self.listar_avaliacoes_service.executar(servico_id, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        # Já vem como lista de dicts da procedure (ver AvaliacaoRepository).
        return jsonify(avaliacoes)

    @login_required
    def solicitar(self, servico_id):
        dados = corpo_json()
        tecnico_ids = dados.get("tecnico_ids") or []
        # Dono do chamado pode solicitar técnicos (mesmo sendo técnico em outra conta).
        if not tecnico_ids:
            return jsonify({"ok": False, "erro": "Informe ao menos um tecnico_id."}), 400

        try:
            solicitacoes = self.solicitar_tecnicos_service.executar(servico_id, tecnico_ids, current_user)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "solicitacoes": [solicitacao.to_dict() for solicitacao in solicitacoes]})

    @login_required
    @apenas_tecnico
    def atribuir_tecnico(self, servico_id):
        """Legado — ver AtribuirTecnicoService."""
        try:
            servico = self.atribuir_tecnico_service.executar(servico_id, current_user.id)
        except DominioError as erro:
            return jsonify({"ok": False, "erro": erro.mensagem}), erro.status_code

        return jsonify({"ok": True, "servico": servico.to_dict()})
