#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#define POLITICA_WRITE_THROUGH 0
#define POLITICA_WRITE_BACK 1
#define SUBSTITUICAO_LRU 1
#define SUBSTITUICAO_ALEATORIA 2
#define ARQUIVO_PADRAO "entrada.txt"

typedef struct {
    int valido;
    uint32_t rotulo;
    int dirty;
    unsigned long long ultimo_uso;
} LinhaCache;

typedef struct {
    char arquivo_entrada[256];
    int politica_escrita;
    int tamanho_linha;
    int numero_linhas;
    int associatividade;
    int tempo_hit;
    int politica_substituicao;
    int tempo_leitura_memoria;
    int tempo_escrita_memoria;
    int numero_conjuntos;
} Configuracao;

typedef struct {
    unsigned long long total_acessos;
    unsigned long long total_leituras;
    unsigned long long total_escritas;
    unsigned long long acertos_leitura;
    unsigned long long acertos_escrita;
    unsigned long long leituras_memoria;
    unsigned long long escritas_memoria;
    unsigned long long relogio;
} Estatisticas;

Configuracao configuracao;
Estatisticas estatisticas;
LinhaCache **cache = NULL;

int eh_potencia_de_dois(int valor) {
    return valor > 0 && (valor & (valor - 1)) == 0;
}

int ler_inteiro_nao_negativo(const char *texto, int *saida) {
    char *fim;
    long valor = strtol(texto, &fim, 10);

    if (*texto == '\0' || *fim != '\0' || valor < 0) {
        return 0;
    }

    *saida = (int)valor;
    return 1;
}

int ler_inteiro_positivo(const char *texto, int *saida) {
    char *fim;
    long valor = strtol(texto, &fim, 10);

    if (*texto == '\0' || *fim != '\0' || valor <= 0) {
        return 0;
    }

    *saida = (int)valor;
    return 1;
}

void mostrar_uso(const char *nome_programa) {
    printf("Uso com arquivo informado:\n");
    printf("  %s arquivo politica_escrita tamanho_linha num_linhas associatividade hit_time politica_substituicao tempo_leitura_mp tempo_escrita_mp\n\n", nome_programa);

    printf("Uso curto no formato do professor:\n");
    printf("  %s politica_escrita tamanho_linha num_linhas associatividade hit_time politica_substituicao tempo_memoria\n", nome_programa);
    printf("  Nesse modo, o arquivo usado sera: %s\n\n", ARQUIVO_PADRAO);

    printf("Uso interativo:\n");
    printf("  %s\n\n", nome_programa);

    printf("Politica de escrita: 0 = write-through, 1 = write-back\n");
    printf("Politica de substituicao: LRU ou ALEATORIA\n");
}

int ler_politica_substituicao(const char *texto) {
    if (strcmp(texto, "LRU") == 0 || strcmp(texto, "lru") == 0 || strcmp(texto, "1") == 0) {
        return SUBSTITUICAO_LRU;
    }

    if (strcmp(texto, "ALEATORIA") == 0 || strcmp(texto, "aleatoria") == 0 ||
        strcmp(texto, "Aleatoria") == 0 || strcmp(texto, "RANDOM") == 0 ||
        strcmp(texto, "random") == 0 || strcmp(texto, "2") == 0) {
        return SUBSTITUICAO_ALEATORIA;
    }

    return -1;
}

int validar_configuracao(void) {
    if (configuracao.politica_escrita != POLITICA_WRITE_THROUGH &&
        configuracao.politica_escrita != POLITICA_WRITE_BACK) {
        printf("Erro: politica de escrita deve ser 0 ou 1.\n");
        return 0;
    }

    if (configuracao.politica_substituicao != SUBSTITUICAO_LRU &&
        configuracao.politica_substituicao != SUBSTITUICAO_ALEATORIA) {
        printf("Erro: politica de substituicao deve ser LRU ou ALEATORIA.\n");
        return 0;
    }

    if (!eh_potencia_de_dois(configuracao.tamanho_linha)) {
        printf("Erro: tamanho da linha deve ser potencia de 2.\n");
        return 0;
    }

    if (!eh_potencia_de_dois(configuracao.numero_linhas)) {
        printf("Erro: numero de linhas deve ser potencia de 2.\n");
        return 0;
    }

    if (!eh_potencia_de_dois(configuracao.associatividade)) {
        printf("Erro: associatividade deve ser potencia de 2.\n");
        return 0;
    }

    if (configuracao.associatividade < 1 || configuracao.associatividade > configuracao.numero_linhas) {
        printf("Erro: associatividade deve ficar entre 1 e o numero de linhas.\n");
        return 0;
    }

    if (configuracao.numero_linhas % configuracao.associatividade != 0) {
        printf("Erro: numero de linhas deve ser divisivel pela associatividade.\n");
        return 0;
    }

    if (configuracao.tempo_hit <= 0 ||
        configuracao.tempo_leitura_memoria <= 0 ||
        configuracao.tempo_escrita_memoria <= 0) {
        printf("Erro: os tempos devem ser maiores que zero.\n");
        return 0;
    }

    configuracao.numero_conjuntos = configuracao.numero_linhas / configuracao.associatividade;
    return 1;
}

int ler_configuracao_interativa(void) {
    char texto_substituicao[32];

    printf("Digite o nome do arquivo de entrada: ");
    if (scanf("%255s", configuracao.arquivo_entrada) != 1) {
        printf("Erro ao ler o arquivo de entrada.\n");
        return 0;
    }

    printf("Digite o tamanho da linha/bloco (em bytes, potencia de 2): ");
    if (scanf("%d", &configuracao.tamanho_linha) != 1) return 0;

    printf("Digite o numero total de linhas da cache (potencia de 2): ");
    if (scanf("%d", &configuracao.numero_linhas) != 1) return 0;

    printf("Digite a associatividade por conjunto (potencia de 2): ");
    if (scanf("%d", &configuracao.associatividade) != 1) return 0;

    printf("Digite o tempo de acesso quando ocorre hit (em nanossegundos): ");
    if (scanf("%d", &configuracao.tempo_hit) != 1) return 0;

    printf("Digite o tempo de leitura da memoria principal (em nanossegundos): ");
    if (scanf("%d", &configuracao.tempo_leitura_memoria) != 1) return 0;

    printf("Digite o tempo de escrita da memoria principal (em nanossegundos): ");
    if (scanf("%d", &configuracao.tempo_escrita_memoria) != 1) return 0;

    printf("Digite a politica de escrita (0 - write-through, 1 - write-back): ");
    if (scanf("%d", &configuracao.politica_escrita) != 1) return 0;

    printf("Digite a politica de substituicao (LRU ou ALEATORIA): ");
    if (scanf("%31s", texto_substituicao) != 1) return 0;

    configuracao.politica_substituicao = ler_politica_substituicao(texto_substituicao);
    return validar_configuracao();
}

int ler_configuracao_com_arquivo(char *argv[]) {
    strncpy(configuracao.arquivo_entrada, argv[1], sizeof(configuracao.arquivo_entrada) - 1);
    configuracao.arquivo_entrada[sizeof(configuracao.arquivo_entrada) - 1] = '\0';

    if (!ler_inteiro_nao_negativo(argv[2], &configuracao.politica_escrita) ||
        !ler_inteiro_positivo(argv[3], &configuracao.tamanho_linha) ||
        !ler_inteiro_positivo(argv[4], &configuracao.numero_linhas) ||
        !ler_inteiro_positivo(argv[5], &configuracao.associatividade) ||
        !ler_inteiro_positivo(argv[6], &configuracao.tempo_hit) ||
        !ler_inteiro_positivo(argv[8], &configuracao.tempo_leitura_memoria) ||
        !ler_inteiro_positivo(argv[9], &configuracao.tempo_escrita_memoria)) {
        printf("Erro: parametros numericos invalidos.\n");
        return 0;
    }

    configuracao.politica_substituicao = ler_politica_substituicao(argv[7]);
    return validar_configuracao();
}

int ler_configuracao_curta(char *argv[]) {
    int tempo_memoria;

    strncpy(configuracao.arquivo_entrada, ARQUIVO_PADRAO, sizeof(configuracao.arquivo_entrada) - 1);
    configuracao.arquivo_entrada[sizeof(configuracao.arquivo_entrada) - 1] = '\0';

    if (!ler_inteiro_nao_negativo(argv[1], &configuracao.politica_escrita) ||
        !ler_inteiro_positivo(argv[2], &configuracao.tamanho_linha) ||
        !ler_inteiro_positivo(argv[3], &configuracao.numero_linhas) ||
        !ler_inteiro_positivo(argv[4], &configuracao.associatividade) ||
        !ler_inteiro_positivo(argv[5], &configuracao.tempo_hit) ||
        !ler_inteiro_positivo(argv[7], &tempo_memoria)) {
        printf("Erro: parametros numericos invalidos.\n");
        return 0;
    }

    configuracao.tempo_leitura_memoria = tempo_memoria;
    configuracao.tempo_escrita_memoria = tempo_memoria;
    configuracao.politica_substituicao = ler_politica_substituicao(argv[6]);

    return validar_configuracao();
}

int ler_configuracao_curta_com_dois_tempos(char *argv[]) {
    strncpy(configuracao.arquivo_entrada, ARQUIVO_PADRAO, sizeof(configuracao.arquivo_entrada) - 1);
    configuracao.arquivo_entrada[sizeof(configuracao.arquivo_entrada) - 1] = '\0';

    if (!ler_inteiro_nao_negativo(argv[1], &configuracao.politica_escrita) ||
        !ler_inteiro_positivo(argv[2], &configuracao.tamanho_linha) ||
        !ler_inteiro_positivo(argv[3], &configuracao.numero_linhas) ||
        !ler_inteiro_positivo(argv[4], &configuracao.associatividade) ||
        !ler_inteiro_positivo(argv[5], &configuracao.tempo_hit) ||
        !ler_inteiro_positivo(argv[7], &configuracao.tempo_leitura_memoria) ||
        !ler_inteiro_positivo(argv[8], &configuracao.tempo_escrita_memoria)) {
        printf("Erro: parametros numericos invalidos.\n");
        return 0;
    }

    configuracao.politica_substituicao = ler_politica_substituicao(argv[6]);
    return validar_configuracao();
}

int ler_configuracao(int argc, char *argv[]) {
    if (argc == 1) {
        return ler_configuracao_interativa();
    }

    if (argc == 8) {
        return ler_configuracao_curta(argv);
    }

    if (argc == 9) {
        return ler_configuracao_curta_com_dois_tempos(argv);
    }

    if (argc == 10) {
        return ler_configuracao_com_arquivo(argv);
    }

    mostrar_uso(argv[0]);
    return 0;
}

void alocar_cache(void) {
    cache = calloc(configuracao.numero_conjuntos, sizeof(LinhaCache *));
    if (cache == NULL) {
        printf("Erro ao alocar cache.\n");
        exit(EXIT_FAILURE);
    }

    for (int i = 0; i < configuracao.numero_conjuntos; i++) {
        cache[i] = calloc(configuracao.associatividade, sizeof(LinhaCache));
        if (cache[i] == NULL) {
            printf("Erro ao alocar conjunto da cache.\n");
            exit(EXIT_FAILURE);
        }
    }
}

void liberar_cache(void) {
    if (cache == NULL) {
        return;
    }

    for (int i = 0; i < configuracao.numero_conjuntos; i++) {
        free(cache[i]);
    }

    free(cache);
}

uint32_t converter_hexadecimal(const char *texto_hexadecimal) {
    return (uint32_t)strtoul(texto_hexadecimal, NULL, 16);
}

int procurar_linha(int indice_conjunto, uint32_t rotulo) {
    for (int i = 0; i < configuracao.associatividade; i++) {
        if (cache[indice_conjunto][i].valido && cache[indice_conjunto][i].rotulo == rotulo) {
            return i;
        }
    }

    return -1;
}

int escolher_linha_para_substituir(int indice_conjunto) {
    int escolhida = 0;

    // Primeiro usa uma linha vazia, se existir.
    for (int i = 0; i < configuracao.associatividade; i++) {
        if (!cache[indice_conjunto][i].valido) {
            return i;
        }
    }

    if (configuracao.politica_substituicao == SUBSTITUICAO_ALEATORIA) {
        return rand() % configuracao.associatividade;
    }

    // LRU: escolhe a linha usada ha mais tempo.
    for (int i = 1; i < configuracao.associatividade; i++) {
        if (cache[indice_conjunto][i].ultimo_uso < cache[indice_conjunto][escolhida].ultimo_uso) {
            escolhida = i;
        }
    }

    return escolhida;
}

void gravar_bloco_dirty_se_precisar(int indice_conjunto, int indice_linha) {
    if (configuracao.politica_escrita == POLITICA_WRITE_BACK &&
        cache[indice_conjunto][indice_linha].valido &&
        cache[indice_conjunto][indice_linha].dirty) {
        estatisticas.escritas_memoria++;
        cache[indice_conjunto][indice_linha].dirty = 0;
    }
}

void carregar_bloco_na_cache(int indice_conjunto, uint32_t rotulo, int marcar_como_dirty) {
    int indice_linha = escolher_linha_para_substituir(indice_conjunto);

    gravar_bloco_dirty_se_precisar(indice_conjunto, indice_linha);

    cache[indice_conjunto][indice_linha].valido = 1;
    cache[indice_conjunto][indice_linha].rotulo = rotulo;
    cache[indice_conjunto][indice_linha].dirty = marcar_como_dirty;
    cache[indice_conjunto][indice_linha].ultimo_uso = ++estatisticas.relogio;
}

int acessar_cache(uint32_t endereco, char operacao) {
    uint32_t numero_bloco = endereco / (uint32_t)configuracao.tamanho_linha;
    int indice_conjunto = (int)(numero_bloco % (uint32_t)configuracao.numero_conjuntos);
    uint32_t rotulo = numero_bloco / (uint32_t)configuracao.numero_conjuntos;
    int indice_linha = procurar_linha(indice_conjunto, rotulo);

    estatisticas.total_acessos++;

    if (operacao == 'R') {
        estatisticas.total_leituras++;
    } else if (operacao == 'W') {
        estatisticas.total_escritas++;
    } else {
        return 0;
    }

    if (indice_linha != -1) {
        cache[indice_conjunto][indice_linha].ultimo_uso = ++estatisticas.relogio;

        if (operacao == 'R') {
            estatisticas.acertos_leitura++;
        } else {
            estatisticas.acertos_escrita++;

            if (configuracao.politica_escrita == POLITICA_WRITE_BACK) {
                cache[indice_conjunto][indice_linha].dirty = 1;
            } else {
                estatisticas.escritas_memoria++;
            }
        }

        return 1;
    }

    // Falha de leitura: busca o bloco na memoria e coloca na cache.
    if (operacao == 'R') {
        estatisticas.leituras_memoria++;
        carregar_bloco_na_cache(indice_conjunto, rotulo, 0);
        return 0;
    }

    // Falha de escrita: write-back aloca; write-through escreve direto na memoria.
    if (configuracao.politica_escrita == POLITICA_WRITE_BACK) {
        estatisticas.leituras_memoria++;
        carregar_bloco_na_cache(indice_conjunto, rotulo, 1);
    } else {
        estatisticas.escritas_memoria++;
    }

    return 0;
}

void atualizar_memoria_ao_final(void) {
    if (configuracao.politica_escrita != POLITICA_WRITE_BACK) {
        return;
    }

    for (int i = 0; i < configuracao.numero_conjuntos; i++) {
        for (int j = 0; j < configuracao.associatividade; j++) {
            if (cache[i][j].valido && cache[i][j].dirty) {
                estatisticas.escritas_memoria++;
                cache[i][j].dirty = 0;
            }
        }
    }
}

void simular_arquivo(void) {
    FILE *arquivo = fopen(configuracao.arquivo_entrada, "r");
    if (arquivo == NULL) {
        perror("Erro ao abrir arquivo de entrada");
        exit(EXIT_FAILURE);
    }

    char linha[128];
    while (fgets(linha, sizeof(linha), arquivo) != NULL) {
        char endereco_hex[32];
        char operacao;

        if (sscanf(linha, "%31s %c", endereco_hex, &operacao) != 2) {
            continue;
        }

        if (operacao != 'R' && operacao != 'W') {
            continue;
        }

        acessar_cache(converter_hexadecimal(endereco_hex), operacao);
    }

    fclose(arquivo);
}

double calcular_taxa(unsigned long long numerador, unsigned long long denominador) {
    if (denominador == 0) {
        return 0.0;
    }

    return (double)numerador / (double)denominador;
}

void imprimir_resultados(FILE *saida) {
    unsigned long long total_acertos = estatisticas.acertos_leitura + estatisticas.acertos_escrita;
    double taxa_acerto_leitura = calcular_taxa(estatisticas.acertos_leitura, estatisticas.total_leituras);
    double taxa_acerto_escrita = calcular_taxa(estatisticas.acertos_escrita, estatisticas.total_escritas);
    double taxa_acerto_global = calcular_taxa(total_acertos, estatisticas.total_acessos);

    double tempo_total =
        (double)estatisticas.total_acessos * (double)configuracao.tempo_hit +
        (double)estatisticas.leituras_memoria * (double)configuracao.tempo_leitura_memoria +
        (double)estatisticas.escritas_memoria * (double)configuracao.tempo_escrita_memoria;

    double tempo_medio = 0.0;
    if (estatisticas.total_acessos > 0) {
        tempo_medio = tempo_total / (double)estatisticas.total_acessos;
    }

    fprintf(saida, "PARAMETROS DE ENTRADA\n");
    fprintf(saida, "Arquivo de entrada: %s\n", configuracao.arquivo_entrada);
    fprintf(saida, "Politica de escrita: %d (%s)\n", configuracao.politica_escrita,
            configuracao.politica_escrita == POLITICA_WRITE_THROUGH ? "write-through" : "write-back");
    fprintf(saida, "Tamanho da linha/bloco: %d bytes\n", configuracao.tamanho_linha);
    fprintf(saida, "Numero de linhas da cache: %d\n", configuracao.numero_linhas);
    fprintf(saida, "Associatividade: %d linha(s) por conjunto\n", configuracao.associatividade);
    fprintf(saida, "Numero de conjuntos: %d\n", configuracao.numero_conjuntos);
    fprintf(saida, "Hit time: %d ns\n", configuracao.tempo_hit);
    fprintf(saida, "Politica de substituicao: %s\n",
            configuracao.politica_substituicao == SUBSTITUICAO_LRU ? "LRU" : "Aleatoria");
    fprintf(saida, "Tempo de leitura da memoria principal: %d ns\n", configuracao.tempo_leitura_memoria);
    fprintf(saida, "Tempo de escrita da memoria principal: %d ns\n", configuracao.tempo_escrita_memoria);

    fprintf(saida, "\nRESULTADOS DA SIMULACAO\n");
    fprintf(saida, "Total de enderecos no arquivo de entrada: %llu\n", estatisticas.total_acessos);
    fprintf(saida, "Total de leituras no arquivo: %llu\n", estatisticas.total_leituras);
    fprintf(saida, "Total de escritas no arquivo: %llu\n", estatisticas.total_escritas);
    fprintf(saida, "Total de leituras da memoria principal: %llu\n", estatisticas.leituras_memoria);
    fprintf(saida, "Total de escritas da memoria principal: %llu\n", estatisticas.escritas_memoria);
    fprintf(saida, "Total de acessos a memoria principal: %llu\n", estatisticas.leituras_memoria + estatisticas.escritas_memoria);

    fprintf(saida, "\nTaxa de acerto (hit rate):\n");
    fprintf(saida, "   - Leitura: %.4f (%llu acertos de %llu leituras)\n",
            taxa_acerto_leitura, estatisticas.acertos_leitura, estatisticas.total_leituras);
    fprintf(saida, "   - Escrita: %.4f (%llu acertos de %llu escritas)\n",
            taxa_acerto_escrita, estatisticas.acertos_escrita, estatisticas.total_escritas);
    fprintf(saida, "   - Global: %.4f (%llu acertos de %llu acessos)\n",
            taxa_acerto_global, total_acertos, estatisticas.total_acessos);

    fprintf(saida, "Tempo medio de acesso da cache: %.4f ns\n", tempo_medio);
}

int main(int argc, char *argv[]) {
    srand((unsigned int)time(NULL));

    if (!ler_configuracao(argc, argv)) {
        return EXIT_FAILURE;
    }

    alocar_cache();
    simular_arquivo();
    atualizar_memoria_ao_final();

    imprimir_resultados(stdout);

    FILE *arquivo_saida = fopen("saida_simulacao.txt", "w");
    if (arquivo_saida == NULL) {
        perror("Erro ao criar arquivo de saida");
        liberar_cache();
        return EXIT_FAILURE;
    }

    imprimir_resultados(arquivo_saida);
    fclose(arquivo_saida);

    liberar_cache();
    return EXIT_SUCCESS;
}
