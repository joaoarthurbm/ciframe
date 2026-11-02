# Persistir o catálogo de sequências de acordes em SQLite

O catálogo de sequências famosas era um `dict` de seis entradas em `main.py`
(`sequencias = {'BmGDA': 0, ...}`), indexado por um id que só existia para casar
com a coluna `SEQ_FAMOSA` pré-computada no CSV. O catálogo cresce agora por
cadastro de visitantes — qualquer pessoa, sem login — e um cadastro que vive em
memória desaparece a cada restart do container, o que é indistinguível de não ter
sido feito. O requisito é explícito: o catálogo passa a sobreviver a reinícios e
cresce sem novo deploy. Não havia decisão anterior a ser revista: até aqui não
existia persistência nenhuma, apenas leitura de um arquivo versionado.

Decidimos introduzir **SQLite**, pela biblioteca padrão do Python (`sqlite3`), em
um arquivo único em `/var/lib/ciframe/ciframe.db`, com o caminho sobrescrevível
pela variável de ambiente `CIFRAME_DB`. O diretório é declarado como `VOLUME` no
`Dockerfile` e o comando documentado passa a incluir
`-v ciframe-data:/var/lib/ciframe`. A escolha por SQLite, e não por um banco
cliente-servidor, decorre do ADR-0001: o projeto roda em um único container
local-only, sem serviços externos, e continua assim. Também descartamos guardar o
catálogo no próprio CSV — o arquivo é lido uma única vez no import, então
cadastro exigiria restart, e escrita read-modify-write em CSV não tem atomicidade
nem unicidade. E descartamos TinyDB e arquivos JSON porque o único problema real
a resolver aqui (impedir que a mesma sequência seja cadastrada duas vezes, de
forma que valha também sob concorrência) é resolvido por uma restrição `UNIQUE`,
que eles não têm.

O caminho do arquivo é a parte não óbvia. A tentação é montar o volume em
`/app/data`, que já é o diretório de dados da aplicação — mas é exatamente ali
que vive o `dataset_final.csv`, aberto com caminho relativo em `main.py`. Um
volume montado sobre `/app/data` substitui o conteúdo do diretório pelo conteúdo
(vazio) do volume, o CSV desaparece e a aplicação falha no import. Por isso o
banco fica em `/var/lib/ciframe`, separado do dado versionado: um é entrada
imutável, o outro é estado gravável, e misturar os dois transforma um erro de
configuração em aplicação que não sobe.

Duas consequências aceitas. A primeira é operacional: o comando de execução
documentado deixa de ser `docker run -p 8080:8080 ciframe` e passa a exigir o
volume; quem esquecer o `-v` perde os cadastros junto com o container, e o
`README.md`/`AGENTS.md` passam a dizer isso explicitamente — documentação
desatualizada aqui não é detalhe, é a diferença entre o requisito cumprido e não
cumprido. A segunda é de escopo: o banco guarda **apenas** o catálogo de
sequências. Músicas e gêneros continuam vindo do CSV em memória, como antes, e a
coluna `SEQ_FAMOSA` deixa de ser lida pelo código mas permanece intacta no
arquivo. Migrar o dataset inteiro para o banco seria uma decisão diferente, maior,
que este ADR não toma.
