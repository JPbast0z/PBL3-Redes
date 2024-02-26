<div align="center">
  <h1>
      Relatório do problema 3: ZapsZap2
  </h1>

  <h3>
    João Pedro da Silva Bastos
  </h3>

  <p>
    Engenharia de Computação – Universidade Estadual de Feira de Santana (UEFS)
    Av. Transnordestina, s/n, Novo Horizonte
    Feira de Santana – BA, Brasil – 44036-900
  </p>

  <center>joaopedro.silvabastos.splash@gmail.com</center>

</div>

# 1. Introdução
Ao longo da evolução da humanidade os meios de comunicação tem se mostrado uma chave crucial para a colaboração e o bom convívio da sociedade. Cartas, telefonemas, e-mails, todos tiveram o seu auge, mas o meio de comunicação mais utilizado atualmente são os aplicativos de trocas de mensagens rápidas. 

Pensando nisso, foi proposto aos membros de uma startup que desenvolvessem um aplicativo de trocas de mensagens instantâneas baseado no modelo peer-to-peer (P2P). O software deve ser descentralizado, e permitir uma troca de mensagens seguras entre os membros do grupo da empresa. O programa deve ser implementado utilizando sockets UDP e garantir que as mensagens sejam exibidas igualmente para todos os membros do grupo.

A solução do problema se deu utilizando a linguagem de programação Python na versão 3.11 e algumas de suas bibliotecas padrões como Json, Socket, threading, uuid, OS, time, copy e plataform . Para a troca de mensagens foi utilizada a arquitetura de rede UDP e para garantir uma troca de mensagens de forma eficiente para todos foi implementado um sistema de confirmação de pacotes.

# 2. Metodologia

## 2.1. Threads
Threads são linhas de execução dentro de um processo maior em um programa de computador. Elas permitem que múltiplas partes do código funcionem simultaneamente, permitindo um uso mais eficiente de recursos e realizando operações mais eficientes. 

Neste programa foram utilizadas 3 threads:
thread_receber: Responsável por receber todos os pacotes enviados por outros usuários.
thread_triagem: Responsável por realizar uma triagem dos pacotes recebidos (mensagens ou pacotes de sincronização).
verif_online: Responsável por verificar quais membros do grupo estão online naquele momento.
atualiza_historico: Responsável por atualizar o histórico de mensagens armazenadas, adicionando-as apenas quando tiver todas as confirmações necessárias.

## 2.3. Pacotes

Para garantir uma troca eficiente de pacotes, foram definidos treze tipos distintos, divididos entre pacotes de mensagem e pacotes de sincronização.

Os pacotes de mensagem convencionais são enviados aos destinatários contendo os seguintes atributos:
- "time": valor marcado no relógio lógico no momento do envio da mensagem.
- "type": identifica o tipo de pacote enviado.
- "conteudo": o próprio conteúdo da mensagem.
- "user": o endereço de quem enviou a mensagem.
- "id": uma identificação única para diferenciar cada pacote.

Todos os pacotes recebidos são tratados na thread “triagem_mensagens” e direcionados para suas respectivas funcionalidades.


Entre os pacotes existem dois tipos de pacotes para sincronização de relógio, utilizados para atualizar o relógio lógico do sistema assim que um usuário se conecta:
1. clockSync: solicita o contador atual do relógio dos outros usuários (contendo apenas o seu tipo e o endereço do solicitante).
2. updateClock: Envia o valor do seu relógio para um usuário que fez uma solicitação (contém o tipo e o valor atual do relógio). 

### 2.3.1 Membros online

Para verificar a desconexão de um membro do grupo, é feito um envio contínuo de pacotes de verificação. Esse envio é feito a cada 0.5 segundos e sempre que um membro não responde esse pacote enviado por 3 vezes seguidas ele é dado como desconectado, até que ele responda a algum pacote de verificação e seja definido como conectado novamente.
Para isso são utilizados os seguintes pacotes:
1. sendTick: Pacote que é enviado para todos os membros do grupo para verificar quais estão conectados no momento.
2. returnTick: É enviado sempre que algum membro do grupo envia um pacote para verificar quem está conectado no momento. É enviado apenas para o membro que fez o pedido.

### 2.3.2 Confirmação de mensagens

A confirmação de mensagens é feita de forma bem didática. Sempre que uma mensagem é enviada, o usuário que enviou guarda o endereço de todos os membros para o qual ele enviou  (que são os usuários que estavam online no momento do envio), e sempre que um usuário recebe uma mensagem ele confirma o recebimento. 
O usuário que enviou guarda as confirmações recebidas, e assim que todos os usuários para qual ele enviou confirmam, ele envia para eles um pacote com tipo “EXIBIR”, autorizando que está mensagem seja adicionada a lista principal de mensagens e que seja exibida.
Para garantir o recebimento do pacote “EXIBIR” a todos os usuários online, o remetente envia este pacote de confirmação para todos que devem exibir a mensagem, e assim que eles recebem este pacote, eles enviam para outros usuários online, buscando garantir uma probabilidade maior de recebimento deste tipo de pacote em questão.

Para isso são utilizados os seguintes pacotes:
1. confirm_msg: Pacote de confirmação de recebimento de mensagem.
2. EXIBIR: Pacote de autorização para exibição da mensagem.

Também é importante salientar que quando uma mensagem é recebida ou enviada ela é adicionada primeiramente a uma lista temporária chamada “historico_temporario” (na prática o historico_temporario é um dicionário, foi chamado de lista para facilitar a compreensão) e só é adicionada à lista de mensagens principal (“historico_mensagens”) quando ocorre a autorização de exibição feita pelo usuário que enviou a mensagem.

### 2.3.3 Recuperação de  mensagens

Quando um usuário desconectado tenta se conectar ao sistema, é feito um pedido para que as mensagens dos históricos de outros usuários sejam enviadas para ele. Nesse processo, a primeira coisa que é feita é o pedido de recuperação para outros usuários, esses usuários confirmam esse pedido e o primeiro a confirmar é o usuário escolhido para ter suas mensagens “extraídas”.

Para facilitar o entendimento irei chamar o usuário que pede a recuperação de mensagens de usuário A e o que compartilha as mensagens de usuário B.

Assim que o usuário B que vai compartilhar seu histórico de mensagens é escolhido, o usuário A que deseja as mensagens vai pedir todos os id’s das mensagens presentes no histórico do usuário B.

Ao recuperar todos os id’s,  é feito o pedido das mensagens presentes no usuário B. Assim que essas mensagens são recuperadas, é feita uma comparação dos id’s recebidos previamente e dos id’s das mensagens recebidas para verificar se todas as mensagens chegaram com sucesso. Caso a confirmação seja feita com sucesso, as mensagens são adicionadas à lista principal e são exibidas, caso contrário, o processo de recuperação é iniciado novamente.

Para isso são utilizados os seguintes pacotes:
1. recoverMSG: Pacote inicial enviado para verificar quem está disponível para compartilhar seu histórico de mensagens e para sinalizar disponibilidade de compartilhamento de histórico de mensagens.
2. returnPedido: Pacote enviado solicitar os id’s das mensagens presentes no histórico.
3. pedido_indices: Pacote onde os id’s são enviados para o usuário que pediu.
4. update_idices: Pacote responsável por guardar os id’s recebidos e solicitar o envio das mensagens do histórico assim que todos os id’s sejam recebidos.
5. pedido_msg: Pacote responsável por enviar todas as mensagens do histórico para o usuário solicitante.
6. envio_recoverMSG: Pacote responsável agrupar as mensagens recebidas e comparar com a lista de id’s recebidos, adicionando na lista principal de mensagens caso o processo seja bem sucedido ou reiniciando o processo caso falhe.

## 2.4 Atualização do histórico de mensagens

A thread “atualizar_historico” funciona de forma linear. A cada 0.2 segundos ela verifica se o histórico temporário de mensagens contém alguma mensagem que ainda não foi confirmada.
É feita uma verificação tanto para mensagens enviadas quanto para mensagens recebidas.
Para as mensagens enviadas, é verificado se o todos os membros para qual a mensagem foi enviada já confirmaram, nesse caso, a mensagem é adicionada ao histórico principal de mensagens, e o pacote do tipo “EXIBIR” é enviado para que os outros usuários tenham a confirmação.
Para as mensagens recebidas, é verificado se a chave “exibir” do dicionário ao qual a mensagem é composta está marcada como True, a partir daí o processo é o mesmo das mensagens enviadas.
Assim que uma mensagem é adicionada no histórico principal ela é retirada do histórico temporário.

# 3 Resultados

A primeira ação que deve ser realizada ao iniciar o programa é selecionar em qual computador o usuário está, visto que a lista de membros de grupos presente no código está definida com endereços IP e portas para os computadores do laboratório (deve ser inserido um número entre 1 e 14, correspondente ao computador que está sendo utilizado). Para que o programa seja testado fora do laboratório, é preciso alterar as informações do dicionário que contém os membros do grupo (membros_grupo), adicionando o endereço IP e porta convenientes para o computador em que está sendo feito o uso. Vale ressaltar que em caso de testes onde o programa é executado várias vezes no mesmo computador, o endereço IP vai ser o mesmo para todos os usuários, porém deve ser utilizado uma porta diferente. O padrão em que os endereços estão sendo registrados é "IP:PORTA", exemplo: "123.0.0.1:1111".

Uma vez selecionado o computador, torna-se possível enviar mensagens para outros usuários online. Caso as mensagens sejam enviadas enquanto os destinatários estão offline, elas serão sincronizadas assim que os usuários iniciarem o programa, graças às funções de sincronização. Vale ressaltar que, em casos onde todos os usuários se desconectem, as mensagens serão perdidas, pois o programa não visa armazenamento não volátil.

Devido ao método de confirmação e confiabilidade de mensagens utilizado, as mensagens só são exibidas caso todos os usuários online a recebam, garantindo que todos estejam sempre visualizando as mesmas mensagens.

Vale ressaltar que visando a portabilidade do programa ele também foi adicionado no docker. Podendo ser baixado via terminal utilizando o comando: "docker pull bast0z/pbl3zapzap:1" e após ser baixado pode ser executado via docker com o comando: "docker run -it --network host bast0z/pbl3zapzap:1".

# 4 Conclusão

Portanto, é possível notar que os objetivos propostos pelo problema foram alcançados com sucesso, empregando conceitos avançados tanto de concorrência quanto de conectividade. A construção do aplicativo de troca de mensagens via socket UDP, utilizando a arquitetura Peer to Peer, permitiu a sincronização eficiente e organizada. Além disso, as mensagens são recuperadas de forma eficaz sempre que um usuário se conecta. O Docker também foi implementado com êxito para assegurar maior portabilidade em diferentes sistemas.

Em futuras atualizações deste projeto, podem ser implementadas melhorias no sistema e atualizações das tecnologias utilizadas, buscando sempre o melhor desempenho e funcionalidade.

# 5 Referências
