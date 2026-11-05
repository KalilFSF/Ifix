"""Regressão isolada: SQLite em memória; sem MySQL, uploads ou e-mails reais.

Executar: python -m unittest discover -s tests -v
"""
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from config import Config

TEST_CONFIG = {
    "TESTING": True, "SECRET_KEY": "teste-aceite-isolado",
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    "CSRF_ENABLED": True, "MAX_CONTENT_LENGTH": 4 * 1024 * 1024,
    "UPLOAD_FOLDER": str(Path(__file__).resolve().parents[1] / "frontend/uploads"),
}
with patch.object(Config, "from_environment", return_value=TEST_CONFIG):
    from app import app
from database import db
import model_registry
from legal import TERMOS_VERSAO, PRIVACIDADE_VERSAO
from modules.usuarios.models.usuario import Usuario


class AceiteCadastroTest(unittest.TestCase):
    def setUp(self):
        self.context = app.app_context()
        self.context.push()
        db.create_all()
        self.client = app.test_client()
        self.csrf = self.client.get("/api/csrf").json["csrf_token"]

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def payload(self):
        return dict(nome="Pessoa de Teste", email="teste@example.test",
                    telefone="31999999999", cpf="52998224725",
                    data_nascimento="1995-01-01", pais="Outro",
                    senha="senha-teste-123", confirmar_senha="senha-teste-123",
                    aceite_termos="1", termos_versao=TERMOS_VERSAO,
                    privacidade_versao=PRIVACIDADE_VERSAO)

    def post(self, role, data):
        return self.client.post(f"/api/cadastro/{role}", data=data,
                                headers={"X-CSRF-Token": self.csrf})

    def test_paginas_publicas_e_links_versionados(self):
        for path, title in [("/termos", "Termos de Uso"), ("/privacidade", "Aviso de Privacidade"),
                            (f"/pages/legal/{TERMOS_VERSAO}/termos.html", "Termos de Uso"),
                            (f"/pages/legal/{PRIVACIDADE_VERSAO}/privacidade.html", "Aviso de Privacidade")]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertIn(title, response.get_data(as_text=True))
            response.close()

    def test_ambos_formularios_exigem_aceite_desmarcado(self):
        from html.parser import HTMLParser
        class Inputs(HTMLParser):
            checkboxes = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "input" and attrs.get("name") == "aceite_termos":
                    self.checkboxes.append(attrs)
        parser = Inputs()
        response = self.client.get("/cadastro")
        parser.feed(response.get_data(as_text=True))
        response.close()
        self.assertEqual(len(parser.checkboxes), 2)
        for attrs in parser.checkboxes:
            self.assertIn("required", attrs)
            self.assertNotIn("checked", attrs)

    def test_api_rejeita_ausente_falso_zero_e_versoes_antigas(self):
        for role in ("cliente", "tecnico"):
            for value in (None, "0", "false", "on", "true"):
                with self.subTest(role=role, value=value):
                    data = self.payload()
                    if value is None:
                        data.pop("aceite_termos")
                    else:
                        data["aceite_termos"] = value
                    response = self.post(role, data)
                    self.assertEqual(response.status_code, 400)
                    self.assertIn("Termos", response.json["erro"])
                    self.assertEqual(Usuario.query.count(), 0)
            for field in ("termos_versao", "privacidade_versao"):
                data = self.payload()
                data[field] = "versao-antiga"
                response = self.post(role, data)
                self.assertEqual(response.status_code, 400)
                self.assertIn("atualizados", response.json["erro"])

    def test_cliente_persiste_versoes_e_data_do_servidor(self):
        data = self.payload()
        data["termos_aceitos_em"] = "1900-01-01"
        self.assertEqual(self.post("cliente", data).status_code, 200)
        usuario = Usuario.query.one()
        self.assertEqual(usuario.termos_versao, TERMOS_VERSAO)
        self.assertEqual(usuario.privacidade_versao, PRIVACIDADE_VERSAO)
        self.assertGreater(usuario.termos_aceitos_em.year, 2020)

    def tecnico_payload(self):
        data = self.payload()
        data.update(especialidade="Notebooks", escolaridade="Técnico",
                    regiao_atendimento="Belo Horizonte",
                    foto_perfil=(io.BytesIO(b"upload simulado"), "foto.png"))
        return data

    @patch("modules.usuarios.services.cadastrar_tecnico_service.salvar_arquivo", return_value="https://example.test/foto.png")
    def test_tecnico_persiste_aceite_com_perfil(self, upload):
        response = self.post("tecnico", self.tecnico_payload())
        self.assertEqual(response.status_code, 200, response.json)
        usuario = Usuario.query.one()
        self.assertIsNotNone(usuario.perfil_tecnico)
        self.assertEqual(usuario.termos_versao, TERMOS_VERSAO)
        self.assertIsNotNone(usuario.termos_aceitos_em)
        upload.assert_called_once()

    @patch("modules.usuarios.services.cadastrar_tecnico_service.salvar_arquivo")
    def test_sem_aceite_nao_dispara_upload(self, upload):
        data = self.tecnico_payload()
        data.pop("aceite_termos")
        self.assertEqual(self.post("tecnico", data).status_code, 400)
        upload.assert_not_called()

    @patch("modules.usuarios.services.cadastrar_tecnico_service.salvar_arquivo", return_value="https://example.test/foto.png")
    @patch("modules.usuarios.services.cadastrar_tecnico_service.PerfilTecnico.criar", side_effect=ValueError("falha simulada"))
    def test_falha_do_perfil_desfaz_conta_e_aceite(self, perfil, upload):
        response = self.post("tecnico", self.tecnico_payload())
        self.assertEqual(response.status_code, 500)
        self.assertEqual(Usuario.query.count(), 0)

    def test_csrf_continua_obrigatorio(self):
        response = self.client.post("/api/cadastro/cliente", data=self.payload())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Usuario.query.count(), 0)

    def test_aceite_nao_e_editavel_pelo_perfil(self):
        from modules.usuarios.services.atualizar_usuario_service import AtualizarUsuarioService
        self.post("cliente", self.payload())
        usuario = Usuario.query.one()
        original = usuario.termos_aceitos_em
        AtualizarUsuarioService().executar(usuario, {"nome": "Nome atualizado", "termos_versao": "forjada", "termos_aceitos_em": "1900"})
        self.assertEqual(usuario.termos_versao, TERMOS_VERSAO)
        self.assertEqual(usuario.termos_aceitos_em, original)


if __name__ == "__main__":
    unittest.main()
