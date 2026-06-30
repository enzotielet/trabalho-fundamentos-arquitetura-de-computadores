#!/usr/bin/env python3
"""
gerar_excel_cache_com_graficos.py

Consolida os arquivos .txt produzidos pelo simulador de cache em:
    1) resultados_cache.csv
    2) resultados_cache_com_graficos.xlsx

O arquivo .xlsx contém:
- aba Resumo;
- aba Dados brutos;
- abas para Cache, Bloco, Associatividade, Substituição e Tráfego;
- gráficos nativos do Excel, alinhados às análises do relatório.

REQUISITO:
    python -m pip install XlsxWriter

USO:
    python gerar_excel_cache_com_graficos.py resultados

A pasta de resultados deve conter os TXT nomeados pelo arquivo
rodar_testes_cache.bat, por exemplo:
    cache_size_64.txt
    block_size_128.txt
    assoc_4.txt
    policy_LRU_64.txt
    traffic_1_8192_128_4.txt
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from typing import Any

try:
    import xlsxwriter
except ModuleNotFoundError:
    print("ERRO: falta instalar a biblioteca XlsxWriter.")
    print("No Prompt de Comando, execute:")
    print("  python -m pip install XlsxWriter")
    raise SystemExit(1)


PADROES: list[tuple[str, str, type]] = [
    ("arquivo_entrada", r"^Arquivo de entrada:\s*(.+)$", str),
    ("politica_escrita", r"^Politica de escrita:\s*(\d+)\s*\(([^)]+)\)", str),
    ("tamanho_bloco_bytes", r"^Tamanho da linha/bloco:\s*(\d+)\s*bytes$", int),
    ("numero_linhas_cache", r"^Numero de linhas da cache:\s*(\d+)$", int),
    ("associatividade", r"^Associatividade:\s*(\d+)\s*linha", int),
    ("numero_conjuntos", r"^Numero de conjuntos:\s*(\d+)$", int),
    ("hit_time_ns", r"^Hit time:\s*(\d+)\s*ns$", int),
    ("politica_substituicao", r"^Politica de substituicao:\s*(.+)$", str),
    ("tempo_leitura_mp_ns", r"^Tempo de leitura da memoria principal:\s*(\d+)\s*ns$", int),
    ("tempo_escrita_mp_ns", r"^Tempo de escrita da memoria principal:\s*(\d+)\s*ns$", int),
    ("total_acessos", r"^Total de enderecos no arquivo de entrada:\s*(\d+)$", int),
    ("total_leituras_arquivo", r"^Total de leituras no arquivo:\s*(\d+)$", int),
    ("total_escritas_arquivo", r"^Total de escritas no arquivo:\s*(\d+)$", int),
    ("leituras_mp", r"^Total de leituras da memoria principal:\s*(\d+)$", int),
    ("escritas_mp", r"^Total de escritas da memoria principal:\s*(\d+)$", int),
    ("acessos_mp", r"^Total de acessos a memoria principal:\s*(\d+)$", int),
    ("taxa_acerto_leitura", r"^\s*-\s*Leitura:\s*([0-9.]+)", float),
    ("taxa_acerto_escrita", r"^\s*-\s*Escrita:\s*([0-9.]+)", float),
    ("taxa_acerto_global", r"^\s*-\s*Global:\s*([0-9.]+)", float),
    ("tempo_medio_acesso_ns", r"^Tempo medio de acesso da cache:\s*([0-9.]+)\s*ns$", float),
]

COLUNAS_CSV = [
    "experimento",
    "arquivo_saida",
    "arquivo_entrada",
    "politica_escrita",
    "tamanho_bloco_bytes",
    "numero_linhas_cache",
    "capacidade_bytes",
    "capacidade_kib",
    "associatividade",
    "numero_conjuntos",
    "hit_time_ns",
    "politica_substituicao",
    "tempo_leitura_mp_ns",
    "tempo_escrita_mp_ns",
    "total_acessos",
    "total_leituras_arquivo",
    "total_escritas_arquivo",
    "leituras_mp",
    "escritas_mp",
    "acessos_mp",
    "taxa_acerto_leitura",
    "taxa_acerto_escrita",
    "taxa_acerto_global",
    "tempo_medio_acesso_ns",
    "rotulo_configuracao",
]

CABECALHOS_EXCEL = {
    "experimento": "Experimento",
    "arquivo_saida": "Arquivo TXT",
    "arquivo_entrada": "Arquivo de entrada",
    "politica_escrita": "Política de escrita",
    "tamanho_bloco_bytes": "Bloco (bytes)",
    "numero_linhas_cache": "Linhas da cache",
    "capacidade_bytes": "Capacidade (bytes)",
    "capacidade_kib": "Capacidade (KiB)",
    "associatividade": "Associatividade",
    "numero_conjuntos": "Conjuntos",
    "hit_time_ns": "Hit time (ns)",
    "politica_substituicao": "Substituição",
    "tempo_leitura_mp_ns": "Leitura MP (ns)",
    "tempo_escrita_mp_ns": "Escrita MP (ns)",
    "total_acessos": "Acessos",
    "total_leituras_arquivo": "Leituras no traço",
    "total_escritas_arquivo": "Escritas no traço",
    "leituras_mp": "Leituras na MP",
    "escritas_mp": "Escritas na MP",
    "acessos_mp": "Acessos à MP",
    "taxa_acerto_leitura": "Taxa de acerto - leitura",
    "taxa_acerto_escrita": "Taxa de acerto - escrita",
    "taxa_acerto_global": "Taxa de acerto global",
    "tempo_medio_acesso_ns": "Tempo médio de acesso (ns)",
    "rotulo_configuracao": "Configuração",
}


def converter(valor: str, tipo: type) -> Any:
    if tipo is int:
        return int(valor)
    if tipo is float:
        return float(valor)
    return valor.strip()


def identificar_experimento(nome_arquivo: str) -> str:
    nome = nome_arquivo.lower()

    if nome.startswith(("cache_size_", "cache_", "tamanho_cache_")):
        return "Cache"
    if nome.startswith(("block_size_", "block_", "bloco_", "tamanho_bloco_")):
        return "Bloco"
    if nome.startswith(("assoc_", "associatividade_")):
        return "Associatividade"
    if nome.startswith(("policy_", "politica_", "substituicao_")):
        return "Substituicao"
    if nome.startswith(("traffic_", "trafego_", "banda_", "memoria_")):
        return "Trafego"
    return "Outros"


def ler_resultado(caminho: Path) -> dict[str, Any]:
    try:
        conteudo = caminho.read_text(encoding="utf-8", errors="replace")
    except OSError as erro:
        raise RuntimeError(f"Não foi possível ler '{caminho.name}': {erro}") from erro

    dados: dict[str, Any] = {
        "arquivo_saida": caminho.name,
        "experimento": identificar_experimento(caminho.name),
    }

    for chave, padrao, tipo in PADROES:
        encontrado = re.search(padrao, conteudo, flags=re.MULTILINE)
        if not encontrado:
            continue

        if chave == "politica_escrita":
            dados[chave] = f"{encontrado.group(1)} ({encontrado.group(2).strip()})"
        else:
            dados[chave] = converter(encontrado.group(1), tipo)

    if "total_acessos" not in dados or "tamanho_bloco_bytes" not in dados:
        raise ValueError(f"'{caminho.name}' não contém uma saída completa do simulador.")

    dados["capacidade_bytes"] = (
        int(dados["tamanho_bloco_bytes"]) * int(dados["numero_linhas_cache"])
    )
    dados["capacidade_kib"] = dados["capacidade_bytes"] / 1024

    dados["rotulo_configuracao"] = (
        f"{dados['politica_escrita']} | "
        f"{dados['capacidade_kib']:g} KiB | "
        f"B={dados['tamanho_bloco_bytes']} | "
        f"A={dados['associatividade']}"
    )
    return dados


def chave_ordenacao(dados: dict[str, Any]) -> tuple:
    ordem = {
        "Cache": 1,
        "Bloco": 2,
        "Associatividade": 3,
        "Substituicao": 4,
        "Trafego": 5,
        "Outros": 9,
    }
    return (
        ordem.get(str(dados.get("experimento")), 9),
        int(dados.get("capacidade_bytes", 0)),
        int(dados.get("tamanho_bloco_bytes", 0)),
        int(dados.get("associatividade", 0)),
        str(dados.get("politica_substituicao", "")),
        str(dados.get("arquivo_saida", "")),
    )


def escrever_csv(destino: Path, linhas: list[dict[str, Any]]) -> None:
    with destino.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=COLUNAS_CSV,
            delimiter=";",
            extrasaction="ignore",
        )
        escritor.writeheader()
        escritor.writerows(linhas)


def configurar_colunas(aba: Any, colunas: list[str]) -> None:
    larguras = {
        "experimento": 16,
        "arquivo_saida": 28,
        "arquivo_entrada": 20,
        "politica_escrita": 20,
        "tamanho_bloco_bytes": 15,
        "numero_linhas_cache": 17,
        "capacidade_bytes": 18,
        "capacidade_kib": 17,
        "associatividade": 16,
        "numero_conjuntos": 13,
        "hit_time_ns": 13,
        "politica_substituicao": 16,
        "tempo_leitura_mp_ns": 16,
        "tempo_escrita_mp_ns": 16,
        "total_acessos": 14,
        "total_leituras_arquivo": 18,
        "total_escritas_arquivo": 18,
        "leituras_mp": 16,
        "escritas_mp": 16,
        "acessos_mp": 16,
        "taxa_acerto_leitura": 22,
        "taxa_acerto_escrita": 22,
        "taxa_acerto_global": 20,
        "tempo_medio_acesso_ns": 23,
        "rotulo_configuracao": 46,
    }

    for indice, coluna in enumerate(colunas):
        aba.set_column(indice, indice, larguras.get(coluna, 16))


def escrever_tabela(
    aba: Any,
    linhas: list[dict[str, Any]],
    colunas: list[str],
    formatos: dict[str, Any],
    nome_tabela: str,
    titulo: str | None = None,
) -> tuple[int, int, dict[str, int]]:
    """Escreve uma tabela e devolve (linha_inicial_dados, linha_final_dados, posições)."""
    linha_titulo = 0
    linha_cabecalho = 0

    if titulo:
        aba.merge_range(0, 0, 0, max(len(colunas) - 1, 1), titulo, formatos["titulo"])
        linha_cabecalho = 2

    for coluna_idx, coluna in enumerate(colunas):
        aba.write(linha_cabecalho, coluna_idx, CABECALHOS_EXCEL[coluna], formatos["cabecalho"])

    linha_inicio_dados = linha_cabecalho + 1

    percentuais = {
        "taxa_acerto_leitura",
        "taxa_acerto_escrita",
        "taxa_acerto_global",
    }

    for linha_idx, linha in enumerate(linhas, start=linha_inicio_dados):
        for coluna_idx, coluna in enumerate(colunas):
            valor = linha.get(coluna, "")
            if coluna in percentuais and isinstance(valor, (int, float)):
                aba.write_number(linha_idx, coluna_idx, valor, formatos["percentual"])
            elif coluna == "tempo_medio_acesso_ns" and isinstance(valor, (int, float)):
                aba.write_number(linha_idx, coluna_idx, valor, formatos["decimal"])
            elif isinstance(valor, (int, float)):
                aba.write_number(linha_idx, coluna_idx, valor, formatos["inteiro"])
            else:
                aba.write(linha_idx, coluna_idx, valor, formatos["texto"])

    linha_final_dados = linha_inicio_dados + len(linhas) - 1

    if linhas:
        aba.add_table(
            linha_cabecalho,
            0,
            linha_final_dados,
            len(colunas) - 1,
            {
                "name": nome_tabela,
                "style": "Table Style Medium 2",
                "columns": [{"header": CABECALHOS_EXCEL[coluna]} for coluna in colunas],
            },
        )

    configurar_colunas(aba, colunas)
    aba.freeze_panes(linha_inicio_dados, 0)
    posicoes = {coluna: idx for idx, coluna in enumerate(colunas)}
    return linha_inicio_dados, linha_final_dados, posicoes


def criar_grafico_duplo(
    workbook: Any,
    aba: Any,
    nome_aba: str,
    linha_inicio: int,
    linha_fim: int,
    coluna_categorias: int,
    coluna_taxa: int,
    coluna_tempo: int,
    titulo: str,
    eixo_x: str,
    posicao: str,
) -> None:
    if linha_fim < linha_inicio:
        return

    grafico = workbook.add_chart({"type": "line"})
    grafico.add_series(
        {
            "name": "Taxa de acerto global",
            "categories": [nome_aba, linha_inicio, coluna_categorias, linha_fim, coluna_categorias],
            "values": [nome_aba, linha_inicio, coluna_taxa, linha_fim, coluna_taxa],
            "line": {"width": 2.25},
            "marker": {"type": "circle", "size": 6},
        }
    )
    grafico.add_series(
        {
            "name": "Tempo médio de acesso (ns)",
            "categories": [nome_aba, linha_inicio, coluna_categorias, linha_fim, coluna_categorias],
            "values": [nome_aba, linha_inicio, coluna_tempo, linha_fim, coluna_tempo],
            "y2_axis": True,
            "line": {"width": 2.25, "dash_type": "dash"},
            "marker": {"type": "square", "size": 6},
        }
    )
    grafico.set_title({"name": titulo})
    grafico.set_x_axis({"name": eixo_x})
    grafico.set_y_axis({"name": "Taxa de acerto global", "num_format": "0.0%"})
    grafico.set_y2_axis({"name": "Tempo médio (ns)"})
    grafico.set_legend({"position": "bottom"})
    grafico.set_size({"width": 760, "height": 360})
    aba.insert_chart(posicao, grafico)


def criar_grafico_politica(
    workbook: Any,
    aba: Any,
    nome_aba: str,
    linhas: list[dict[str, Any]],
    formatos: dict[str, Any],
) -> None:
    """
    Compara LRU e ALEATÓRIA para a mesma quantidade de linhas da cache.

    A tabela auxiliar fica à direita da tabela principal, sem sobrescrever
    dados nem ficar oculta. Isso evita gráficos vazios ou distorcidos no Excel.
    """
    if not linhas:
        return

    por_linhas: dict[int, dict[str, dict[str, Any]]] = {}
    for linha in linhas:
        quantidade_linhas = int(linha["numero_linhas_cache"])
        politica = str(linha["politica_substituicao"]).strip().upper()

        # Aceita tanto "Aleatoria" quanto "ALEATORIA".
        if politica == "LRU":
            chave_politica = "LRU"
        elif politica in {"ALEATORIA", "ALEATÓRIA", "RANDOM"}:
            chave_politica = "ALEATORIA"
        else:
            continue

        por_linhas.setdefault(quantidade_linhas, {})[chave_politica] = linha

    # Mantém apenas comparações completas: uma linha LRU e uma ALEATÓRIA
    # para o mesmo número de linhas da cache.
    pares = {
        quantidade: dados
        for quantidade, dados in por_linhas.items()
        if "LRU" in dados and "ALEATORIA" in dados
    }

    if not pares:
        aba.write(
            "A22",
            "Não foram encontrados pares LRU e ALEATÓRIA com a mesma configuração.",
            formatos["nota"],
        )
        return

    # A tabela principal ocupa A:Y (25 colunas). A auxiliar começa em AB,
    # preservando toda a tabela original e evitando conflito com os gráficos.
    linha_aux = 2
    col_aux = len(COLUNAS_CSV) + 2

    aba.write(
        linha_aux - 1,
        col_aux,
        "Dados auxiliares — política de substituição",
        formatos["titulo"],
    )

    cabecalhos = [
        "Linhas",
        "LRU - Hit",
        "Aleatória - Hit",
        "LRU - Tempo",
        "Aleatória - Tempo",
    ]
    aba.write_row(linha_aux, col_aux, cabecalhos, formatos["cabecalho"])

    for linha_excel, quantidade_linhas in enumerate(sorted(pares), start=linha_aux + 1):
        lru = pares[quantidade_linhas]["LRU"]
        aleatoria = pares[quantidade_linhas]["ALEATORIA"]

        aba.write_number(linha_excel, col_aux, quantidade_linhas, formatos["inteiro"])
        aba.write_number(
            linha_excel,
            col_aux + 1,
            float(lru["taxa_acerto_global"]),
            formatos["percentual"],
        )
        aba.write_number(
            linha_excel,
            col_aux + 2,
            float(aleatoria["taxa_acerto_global"]),
            formatos["percentual"],
        )
        aba.write_number(
            linha_excel,
            col_aux + 3,
            float(lru["tempo_medio_acesso_ns"]),
            formatos["decimal"],
        )
        aba.write_number(
            linha_excel,
            col_aux + 4,
            float(aleatoria["tempo_medio_acesso_ns"]),
            formatos["decimal"],
        )

    linha_fim = linha_aux + len(pares)

    grafico_hit = workbook.add_chart({"type": "line"})
    grafico_hit.add_series(
        {
            "name": [nome_aba, linha_aux, col_aux + 1],
            "categories": [nome_aba, linha_aux + 1, col_aux, linha_fim, col_aux],
            "values": [nome_aba, linha_aux + 1, col_aux + 1, linha_fim, col_aux + 1],
            "line": {"width": 2.25},
            "marker": {"type": "circle", "size": 6},
        }
    )
    grafico_hit.add_series(
        {
            "name": [nome_aba, linha_aux, col_aux + 2],
            "categories": [nome_aba, linha_aux + 1, col_aux, linha_fim, col_aux],
            "values": [nome_aba, linha_aux + 1, col_aux + 2, linha_fim, col_aux + 2],
            "line": {"width": 2.25, "dash_type": "dash"},
            "marker": {"type": "square", "size": 6},
        }
    )
    grafico_hit.set_title({"name": "Política de substituição: taxa de acerto"})
    grafico_hit.set_x_axis({"name": "Número de linhas da cache"})
    grafico_hit.set_y_axis({"name": "Taxa de acerto global", "num_format": "0.0%"})
    grafico_hit.set_legend({"position": "bottom"})
    grafico_hit.set_size({"width": 760, "height": 360})
    aba.insert_chart("A22", grafico_hit)

    grafico_tempo = workbook.add_chart({"type": "line"})
    grafico_tempo.add_series(
        {
            "name": [nome_aba, linha_aux, col_aux + 3],
            "categories": [nome_aba, linha_aux + 1, col_aux, linha_fim, col_aux],
            "values": [nome_aba, linha_aux + 1, col_aux + 3, linha_fim, col_aux + 3],
            "line": {"width": 2.25},
            "marker": {"type": "circle", "size": 6},
        }
    )
    grafico_tempo.add_series(
        {
            "name": [nome_aba, linha_aux, col_aux + 4],
            "categories": [nome_aba, linha_aux + 1, col_aux, linha_fim, col_aux],
            "values": [nome_aba, linha_aux + 1, col_aux + 4, linha_fim, col_aux + 4],
            "line": {"width": 2.25, "dash_type": "dash"},
            "marker": {"type": "square", "size": 6},
        }
    )
    grafico_tempo.set_title({"name": "Política de substituição: tempo médio"})
    grafico_tempo.set_x_axis({"name": "Número de linhas da cache"})
    grafico_tempo.set_y_axis({"name": "Tempo médio de acesso (ns)"})
    grafico_tempo.set_legend({"position": "bottom"})
    grafico_tempo.set_size({"width": 760, "height": 360})
    aba.insert_chart("A42", grafico_tempo)

    # Mostra a tabela auxiliar; ela é a fonte direta dos dois gráficos.
    aba.set_column(col_aux, col_aux + 4, 18)

def criar_grafico_trafego(
    workbook: Any,
    aba: Any,
    nome_aba: str,
    linha_inicio: int,
    linha_fim: int,
    posicoes: dict[str, int],
) -> None:
    if linha_fim < linha_inicio:
        return

    grafico = workbook.add_chart({"type": "column", "subtype": "stacked"})
    grafico.add_series(
        {
            "name": "Leituras na MP",
            "categories": [nome_aba, linha_inicio, posicoes["rotulo_configuracao"], linha_fim, posicoes["rotulo_configuracao"]],
            "values": [nome_aba, linha_inicio, posicoes["leituras_mp"], linha_fim, posicoes["leituras_mp"]],
        }
    )
    grafico.add_series(
        {
            "name": "Escritas na MP",
            "categories": [nome_aba, linha_inicio, posicoes["rotulo_configuracao"], linha_fim, posicoes["rotulo_configuracao"]],
            "values": [nome_aba, linha_inicio, posicoes["escritas_mp"], linha_fim, posicoes["escritas_mp"]],
        }
    )
    grafico.set_title({"name": "Tráfego da memória principal"})
    grafico.set_x_axis({"name": "Configuração", "label_position": "low"})
    grafico.set_y_axis({"name": "Acessos à memória principal"})
    grafico.set_legend({"position": "bottom"})
    grafico.set_size({"width": 960, "height": 420})
    aba.insert_chart("A22", grafico)


def criar_planilha(destino: Path, linhas: list[dict[str, Any]]) -> None:
    workbook = xlsxwriter.Workbook(str(destino))
    workbook.set_properties(
        {
            "title": "Análise dos Impactos na Memória Cache",
            "subject": "Resultados do simulador de cache",
            "author": "Simulador de Cache",
            "comments": "Planilha gerada automaticamente a partir dos TXT do simulador.",
        }
    )

    formatos = {
        "titulo": workbook.add_format(
            {
                "bold": True,
                "font_size": 15,
                "font_color": "#FFFFFF",
                "bg_color": "#1F4E78",
                "align": "center",
                "valign": "vcenter",
            }
        ),
        "cabecalho": workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": "#1F4E78",
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "border": 1,
            }
        ),
        "texto": workbook.add_format({"border": 1, "valign": "vcenter"}),
        "inteiro": workbook.add_format({"border": 1, "num_format": "#,##0"}),
        "decimal": workbook.add_format({"border": 1, "num_format": "0.0000"}),
        "percentual": workbook.add_format({"border": 1, "num_format": "0.00%"}),
        "nota": workbook.add_format({"italic": True, "font_color": "#595959", "text_wrap": True}),
        "kpi_rotulo": workbook.add_format({"bold": True, "bg_color": "#D9EAF7", "border": 1}),
        "kpi_valor": workbook.add_format({"bg_color": "#EAF3F8", "border": 1, "num_format": "#,##0"}),
    }

    abas_por_experimento = {
        "Cache": "Tamanho da Cache",
        "Bloco": "Tamanho do Bloco",
        "Associatividade": "Associatividade",
        "Substituicao": "Política Substituição",
        "Trafego": "Tráfego da MP",
        "Outros": "Outros",
    }

    # Aba Resumo.
    resumo = workbook.add_worksheet("Resumo")
    resumo.set_tab_color("#1F4E78")
    resumo.merge_range("A1:H1", "Análise dos Impactos na Memória Cache", formatos["titulo"])
    resumo.set_row(0, 24)
    resumo.write("A3", "Arquivo Excel gerado a partir dos TXT de saída do simulador.", formatos["nota"])
    resumo.write("A5", "Total de execuções lidas", formatos["kpi_rotulo"])
    resumo.write_number("B5", len(linhas), formatos["kpi_valor"])
    resumo.write("A6", "Total de acessos por execução", formatos["kpi_rotulo"])
    resumo.write_number("B6", int(linhas[0]["total_acessos"]) if linhas else 0, formatos["kpi_valor"])
    resumo.write("A8", "Abas geradas", formatos["kpi_rotulo"])

    nomes_abas_geradas = []
    for experimento, nome_aba in abas_por_experimento.items():
        if any(linha["experimento"] == experimento for linha in linhas):
            nomes_abas_geradas.append(nome_aba)

    for indice, nome_aba in enumerate(nomes_abas_geradas, start=8):
        resumo.write(indice, 0, nome_aba, formatos["texto"])

    resumo.write(
        "D3",
        "Leitura da planilha:\n"
        "• Cada aba contém a tabela de resultados do experimento.\n"
        "• As taxas são exibidas como porcentagens.\n"
        "• Os gráficos usam taxa de acerto global, tempo médio de acesso e/ou tráfego da MP.",
        formatos["nota"],
    )
    resumo.set_column("A:A", 27)
    resumo.set_column("B:B", 18)
    resumo.set_column("D:H", 18)
    resumo.set_row(2, 52)

    # Dados brutos.
    dados = workbook.add_worksheet("Dados brutos")
    dados.set_tab_color("#5B9BD5")
    escrever_tabela(
        dados,
        linhas,
        COLUNAS_CSV,
        formatos,
        "DadosBrutos",
        "Dados brutos de todas as execuções",
    )

    # Abas específicas por experimento.
    for experimento, nome_aba in abas_por_experimento.items():
        dados_experimento = [linha for linha in linhas if linha["experimento"] == experimento]
        if not dados_experimento:
            continue

        nome_aba_excel = nome_aba[:31]
        aba = workbook.add_worksheet(nome_aba_excel)
        aba.set_tab_color("#70AD47")
        linha_inicio, linha_fim, posicoes = escrever_tabela(
            aba,
            dados_experimento,
            COLUNAS_CSV,
            formatos,
            "Tabela" + re.sub(r"[^A-Za-z0-9]", "", experimento),
            f"Resultados — {nome_aba}",
        )

        if experimento == "Cache":
            criar_grafico_duplo(
                workbook,
                aba,
                nome_aba_excel,
                linha_inicio,
                linha_fim,
                posicoes["capacidade_kib"],
                posicoes["taxa_acerto_global"],
                posicoes["tempo_medio_acesso_ns"],
                "Impacto do tamanho da cache",
                "Capacidade da cache (KiB)",
                "A22",
            )
        elif experimento == "Bloco":
            criar_grafico_duplo(
                workbook,
                aba,
                nome_aba_excel,
                linha_inicio,
                linha_fim,
                posicoes["tamanho_bloco_bytes"],
                posicoes["taxa_acerto_global"],
                posicoes["tempo_medio_acesso_ns"],
                "Impacto do tamanho do bloco",
                "Tamanho do bloco (bytes)",
                "A22",
            )
        elif experimento == "Associatividade":
            criar_grafico_duplo(
                workbook,
                aba,
                nome_aba_excel,
                linha_inicio,
                linha_fim,
                posicoes["associatividade"],
                posicoes["taxa_acerto_global"],
                posicoes["tempo_medio_acesso_ns"],
                "Impacto da associatividade",
                "Associatividade (linhas por conjunto)",
                "A22",
            )
        elif experimento == "Substituicao":
            criar_grafico_politica(workbook, aba, nome_aba_excel, dados_experimento, formatos)
        elif experimento == "Trafego":
            criar_grafico_trafego(workbook, aba, nome_aba_excel, linha_inicio, linha_fim, posicoes)

    workbook.close()


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python gerar_excel_cache_com_graficos.py <pasta_com_txts>")
        return 1

    pasta = Path(sys.argv[1]).expanduser().resolve()

    if not pasta.is_dir():
        print(f"ERRO: a pasta não existe: {pasta}")
        return 1

    nomes_ignorados = {
        "saida_simulacao.txt",
        "resultados_cache.csv",
        "resultado_validacao.txt",
    }

    arquivos = sorted(
        arquivo
        for arquivo in pasta.glob("*.txt")
        if arquivo.name.lower() not in nomes_ignorados
    )

    if not arquivos:
        print(f"ERRO: nenhum TXT foi encontrado em: {pasta}")
        return 1

    resultados: list[dict[str, Any]] = []
    ignorados: list[str] = []

    for arquivo in arquivos:
        try:
            resultados.append(ler_resultado(arquivo))
        except (RuntimeError, ValueError) as erro:
            ignorados.append(str(erro))

    if not resultados:
        print("ERRO: nenhum TXT válido do simulador foi encontrado.")
        for erro in ignorados:
            print(" -", erro)
        return 1

    resultados.sort(key=chave_ordenacao)

    destino_csv = pasta / "resultados_cache.csv"
    destino_xlsx = pasta / "resultados_cache_com_graficos.xlsx"

    escrever_csv(destino_csv, resultados)
    criar_planilha(destino_xlsx, resultados)

    print(f"OK: {len(resultados)} execuções consolidadas.")
    print(f"CSV criado:   {destino_csv}")
    print(f"Excel criado: {destino_xlsx}")

    if ignorados:
        print("\nArquivos ignorados:")
        for erro in ignorados:
            print(" -", erro)

    print("\nO Excel contém abas e gráficos para cada experimento reconhecido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
