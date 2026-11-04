"""Entrada legada: não importa app nem executa DDL ao ser importada."""
if __name__ == "__main__":
    import runpy
    from pathlib import Path
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "inicializar_mysql.py"), run_name="__main__")
