@echo off
setlocal EnableExtensions
REM ===============================================================
REM Reproduz os testes do relatorio "Analise dos Impactos na Memoria Cache"
REM Coloque este .bat, simula_cache.exe e entrada2.txt na mesma pasta.
REM Se o executavel tiver outro nome, altere a linha abaixo.
REM ===============================================================
set "EXE=simula_cache.exe"
set "TRACE=entrada2.txt"
set "OUT=resultados"

if not exist "%EXE%" (
  echo ERRO: nao encontrei %EXE% nesta pasta.
  pause
  exit /b 1
)
if not exist "%TRACE%" (
  echo ERRO: nao encontrei %TRACE% nesta pasta.
  pause
  exit /b 1
)
if not exist "%OUT%" mkdir "%OUT%"

REM IMPORTANTE: os testes ALEATORIA reproduzem os numeros do relatorio
REM somente se o fonte usar srand(20260624U), e nao srand(time(NULL)).

REM 1. Impacto do tamanho da cache
"%EXE%" "%TRACE%" 0 128 8    4 4 LRU 60 60 > "%OUT%\cache_size_8.txt"
"%EXE%" "%TRACE%" 0 128 16   4 4 LRU 60 60 > "%OUT%\cache_size_16.txt"
"%EXE%" "%TRACE%" 0 128 32   4 4 LRU 60 60 > "%OUT%\cache_size_32.txt"
"%EXE%" "%TRACE%" 0 128 64   4 4 LRU 60 60 > "%OUT%\cache_size_64.txt"
"%EXE%" "%TRACE%" 0 128 128  4 4 LRU 60 60 > "%OUT%\cache_size_128.txt"
"%EXE%" "%TRACE%" 0 128 256  4 4 LRU 60 60 > "%OUT%\cache_size_256.txt"
"%EXE%" "%TRACE%" 0 128 512  4 4 LRU 60 60 > "%OUT%\cache_size_512.txt"
"%EXE%" "%TRACE%" 0 128 1024 4 4 LRU 60 60 > "%OUT%\cache_size_1024.txt"

REM 2. Impacto do tamanho do bloco (capacidade mantida em 8 KiB)
"%EXE%" "%TRACE%" 0 8    1024 2 4 LRU 60 60 > "%OUT%\block_size_8.txt"
"%EXE%" "%TRACE%" 0 16   512  2 4 LRU 60 60 > "%OUT%\block_size_16.txt"
"%EXE%" "%TRACE%" 0 32   256  2 4 LRU 60 60 > "%OUT%\block_size_32.txt"
"%EXE%" "%TRACE%" 0 64   128  2 4 LRU 60 60 > "%OUT%\block_size_64.txt"
"%EXE%" "%TRACE%" 0 128  64   2 4 LRU 60 60 > "%OUT%\block_size_128.txt"
"%EXE%" "%TRACE%" 0 256  32   2 4 LRU 60 60 > "%OUT%\block_size_256.txt"
"%EXE%" "%TRACE%" 0 512  16   2 4 LRU 60 60 > "%OUT%\block_size_512.txt"
"%EXE%" "%TRACE%" 0 1024 8    2 4 LRU 60 60 > "%OUT%\block_size_1024.txt"
"%EXE%" "%TRACE%" 0 2048 4    2 4 LRU 60 60 > "%OUT%\block_size_2048.txt"
"%EXE%" "%TRACE%" 0 4096 2    2 4 LRU 60 60 > "%OUT%\block_size_4096.txt"

REM 3. Impacto da associatividade (8 KiB; write-back)
"%EXE%" "%TRACE%" 1 128 64 1  4 LRU 60 60 > "%OUT%\assoc_1.txt"
"%EXE%" "%TRACE%" 1 128 64 2  4 LRU 60 60 > "%OUT%\assoc_2.txt"
"%EXE%" "%TRACE%" 1 128 64 4  4 LRU 60 60 > "%OUT%\assoc_4.txt"
"%EXE%" "%TRACE%" 1 128 64 8  4 LRU 60 60 > "%OUT%\assoc_8.txt"
"%EXE%" "%TRACE%" 1 128 64 16 4 LRU 60 60 > "%OUT%\assoc_16.txt"
"%EXE%" "%TRACE%" 1 128 64 32 4 LRU 60 60 > "%OUT%\assoc_32.txt"
"%EXE%" "%TRACE%" 1 128 64 64 4 LRU 60 60 > "%OUT%\assoc_64.txt"

REM 4. Impacto da politica de substituicao
"%EXE%" "%TRACE%" 0 128 16   4 4 LRU       60 60 > "%OUT%\policy_LRU_16.txt"
"%EXE%" "%TRACE%" 0 128 16   4 4 ALEATORIA 60 60 > "%OUT%\policy_ALEATORIA_16.txt"
"%EXE%" "%TRACE%" 0 128 32   4 4 LRU       60 60 > "%OUT%\policy_LRU_32.txt"
"%EXE%" "%TRACE%" 0 128 32   4 4 ALEATORIA 60 60 > "%OUT%\policy_ALEATORIA_32.txt"
"%EXE%" "%TRACE%" 0 128 64   4 4 LRU       60 60 > "%OUT%\policy_LRU_64.txt"
"%EXE%" "%TRACE%" 0 128 64   4 4 ALEATORIA 60 60 > "%OUT%\policy_ALEATORIA_64.txt"
"%EXE%" "%TRACE%" 0 128 128  4 4 LRU       60 60 > "%OUT%\policy_LRU_128.txt"
"%EXE%" "%TRACE%" 0 128 128  4 4 ALEATORIA 60 60 > "%OUT%\policy_ALEATORIA_128.txt"
"%EXE%" "%TRACE%" 0 128 256  4 4 LRU       60 60 > "%OUT%\policy_LRU_256.txt"
"%EXE%" "%TRACE%" 0 128 256  4 4 ALEATORIA 60 60 > "%OUT%\policy_ALEATORIA_256.txt"
"%EXE%" "%TRACE%" 0 128 512  4 4 LRU       60 60 > "%OUT%\policy_LRU_512.txt"
"%EXE%" "%TRACE%" 0 128 512  4 4 ALEATORIA 60 60 > "%OUT%\policy_ALEATORIA_512.txt"
"%EXE%" "%TRACE%" 0 128 1024 4 4 LRU       60 60 > "%OUT%\policy_LRU_1024.txt"
"%EXE%" "%TRACE%" 0 128 1024 4 4 ALEATORIA 60 60 > "%OUT%\policy_ALEATORIA_1024.txt"

REM 5. Trafego/largura de banda da memoria
REM Formato do nome: traffic_politica_capacidade_bloco_associatividade.txt
"%EXE%" "%TRACE%" 0 64  128 2 4 LRU 60 60 > "%OUT%\traffic_0_8192_64_2.txt"
"%EXE%" "%TRACE%" 0 64  128 4 4 LRU 60 60 > "%OUT%\traffic_0_8192_64_4.txt"
"%EXE%" "%TRACE%" 0 128 64  2 4 LRU 60 60 > "%OUT%\traffic_0_8192_128_2.txt"
"%EXE%" "%TRACE%" 0 128 64  4 4 LRU 60 60 > "%OUT%\traffic_0_8192_128_4.txt"
"%EXE%" "%TRACE%" 0 64  256 2 4 LRU 60 60 > "%OUT%\traffic_0_16384_64_2.txt"
"%EXE%" "%TRACE%" 0 64  256 4 4 LRU 60 60 > "%OUT%\traffic_0_16384_64_4.txt"
"%EXE%" "%TRACE%" 0 128 128 2 4 LRU 60 60 > "%OUT%\traffic_0_16384_128_2.txt"
"%EXE%" "%TRACE%" 0 128 128 4 4 LRU 60 60 > "%OUT%\traffic_0_16384_128_4.txt"
"%EXE%" "%TRACE%" 1 64  128 2 4 LRU 60 60 > "%OUT%\traffic_1_8192_64_2.txt"
"%EXE%" "%TRACE%" 1 64  128 4 4 LRU 60 60 > "%OUT%\traffic_1_8192_64_4.txt"
"%EXE%" "%TRACE%" 1 128 64  2 4 LRU 60 60 > "%OUT%\traffic_1_8192_128_2.txt"
"%EXE%" "%TRACE%" 1 128 64  4 4 LRU 60 60 > "%OUT%\traffic_1_8192_128_4.txt"
"%EXE%" "%TRACE%" 1 64  256 2 4 LRU 60 60 > "%OUT%\traffic_1_16384_64_2.txt"
"%EXE%" "%TRACE%" 1 64  256 4 4 LRU 60 60 > "%OUT%\traffic_1_16384_64_4.txt"
"%EXE%" "%TRACE%" 1 128 128 2 4 LRU 60 60 > "%OUT%\traffic_1_16384_128_2.txt"
"%EXE%" "%TRACE%" 1 128 128 4 4 LRU 60 60 > "%OUT%\traffic_1_16384_128_4.txt"

echo.
echo Testes concluidos. Os arquivos estao na pasta "%OUT%".
pause
