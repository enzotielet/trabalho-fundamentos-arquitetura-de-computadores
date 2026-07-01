O arquivo rodar_testes_cache executa todos os testes que foram usados para a analise da perfomance do programa \n
O arquivo gerar_excel_cache_com_graficos faz a mesma coisa só que já cria graficos no excel
Os resultados das simulações estão na pasta resultados 
O executavel pode gerar a simulação com duas formas de entrada possiveis, ou executando ele e ele pergunta o valor de cada parâmetro ou é possivel roda o nome dele seguido das variaveis de entrada. 
Ex: simula_cache entrada2.txt 1 128 64 4 2 LRU 60 59
O primeiro parametro é o arquivo de entrada
O segundo parametro é se é write-back ou write-through, sendo 0 - write-through e 1 - write-back
O terceiro é o tamanho do bloco 
O quarto é o numero de linhas 
O quinto é a associatividade, linhas por conjunto 
O sexto é o hit time, em ns
o sétimo é tempo de leitura da memoria principal, em ns
o oitavo é tempo de escrita da memoria principal, em ns
