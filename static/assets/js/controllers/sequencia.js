angular.module('deciframeApp').controller('SequenciaController', function($http, $window, ngProgressFactory, $anchorScroll, $location, GENEROS) {
  var COR_PADRAO = '#2E1C74';

  var vm = this;
  vm.sequenciasFamosas = [];
  vm.minhaSequencia = {};
  vm.isSearching = false;
  vm.showSearchResultsCount = false;
  vm.esfigeSpeech =  "";
  vm.musics = [];
  vm.generos = GENEROS;
  vm.meuGenero = "";
  vm.progressbar = ngProgressFactory.createInstance();

  // cadastro
  vm.novaSequencia = "";
  vm.erroCadastro = "";
  vm.erroCatalogo = "";
  vm.salvando = false;

  // O catálogo vem do backend: as 6 sequências originais + as cadastradas por
  // qualquer visitante. Antes eram 4 objetos hardcoded aqui, e EmG / CA7DmG7
  // não existiam na tela.
  var mapear = function(registro) {
    return {
      'id': registro.id,
      'nome': registro.nome,
      'chave': registro.chave,
      'acordes': (registro.acordes || []).map(function(acorde) {
        return { 'acorde': acorde, 'cor': COR_PADRAO };
      })
    };
  };

  var buscarPorId = function(id) {
    for (var i = 0; i < vm.sequenciasFamosas.length; i++) {
      if (vm.sequenciasFamosas[i].id === id) {
        return vm.sequenciasFamosas[i];
      }
    }
    return null;
  };

  var carregarCatalogo = function() {
    $http.get("sequencias")
      .success(function(registros) {
        vm.sequenciasFamosas = registros.map(mapear);
        vm.erroCatalogo = "";
      })
      .error(function() {
        vm.erroCatalogo = "Não foi possível carregar o catálogo de sequências.";
      });
  };

  vm.temAcorde = function(acordeon) {
    if (!acordeon || !vm.minhaSequencia || !vm.minhaSequencia.acordes) {
      return false;
    }
    var alvo = acordeon.acorde;
    for (var i = 0; i < vm.minhaSequencia.acordes.length; i++) {
      if (vm.minhaSequencia.acordes[i].acorde === alvo) {
        return true;
      }
    }
    return false;
  };

  vm.pesquisarPorSequencia = function(sequencia) {
    if (sequencia) {
      vm.minhaSequencia = sequencia;
    }
    if (!vm.minhaSequencia || !vm.minhaSequencia.id) {
      return;
    }
    vm.progressbar.start();
    vm.esfigeSpeech = "Procurando músicas com base na sequencia...";
    vm.isSearching = true;
    vm.musics = [];

    var searchString = "similares?sequencia_id=".concat(vm.minhaSequencia.id);
    if (vm.meuGenero !== "" && vm.meuGenero !== null) {
      searchString += "&generos="+vm.meuGenero;
    }
    $http.get(searchString)
      .success(function(data) {
        vm.progressbar.complete();
        vm.esfigeSpeech = "Encontrei essas músicas";
        vm.isSearching = false;
        vm.showSearchResultsCount = true;
        vm.musics = data;
      })
      .error(function() {
        vm.esfigeSpeech = "Ops! Algo errado.";
        vm.isSearching = false;
        vm.showSearchResultsCount = false;
      });
  };

  vm.parsearAcordes = function(texto) {
    if (!texto) {
      return [];
    }
    return texto.split(/[\s,;]+/).filter(function(token) {
      return token.length > 0;
    });
  };

  vm.adicionarSequencia = function() {
    var acordes = vm.parsearAcordes(vm.novaSequencia);
    vm.erroCadastro = "";

    if (acordes.length < 2) {
      vm.erroCadastro = "Informe pelo menos dois acordes (ex.: Bm G D A).";
      return;
    }

    vm.salvando = true;
    $http.post("sequencias", { 'acordes': acordes })
      .success(function(registro) {
        vm.salvando = false;
        vm.novaSequencia = "";
        var nova = mapear(registro);
        // entra no topo para o usuário ver o que acabou de cadastrar; o servidor
        // devolve na ordem de id, então um reload a move para o fim da lista
        vm.sequenciasFamosas.unshift(nova);
        vm.pesquisarPorSequencia(nova);
      })
      .error(function(data, status) {
        vm.salvando = false;
        if (status === 409) {
          vm.erroCadastro = "Essa sequência já está no catálogo.";
          var existente = data ? buscarPorId(data.id) : null;
          if (existente) {
            vm.novaSequencia = "";
            vm.pesquisarPorSequencia(existente);
          }
        } else if (data && data.erro) {
          vm.erroCadastro = data.erro;
        } else {
          vm.erroCadastro = "Não foi possível cadastrar a sequência.";
        }
      });
  };

  vm.limparPesquisa = function() {
    vm.minhaSequencia = {};
    vm.musics = [];
  }

  vm.goToLirics = function(music) {
    $window.open(music.url);
  };

  vm.goToResults = function() {
    vm.showSearchResultsCount = false;
    $("body").animate({scrollTop: $("#results").offset().top}, "slow");
  };

  carregarCatalogo();
});
