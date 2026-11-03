angular.module('deciframeApp').controller('SequenciaController', function($http, $window, ngProgressFactory, $anchorScroll, $location, GENEROS) {
  var COR_ACORDE = '#2E1C74';

  var vm = this;
  vm.sequenciasFamosas = [];
  vm.acordesDisponiveis = [];
  vm.novaSequencia = { nome: '', acordes: [] };
  vm.novoAcorde = '';
  vm.erroCadastro = '';
  vm.erroCatalogo = '';
  vm.salvando = false;
  vm.carregandoCatalogo = true;
  vm.minhaSequencia = {};
  vm.isSearching = false;
  vm.showSearchResultsCount = false;
  vm.esfigeSpeech = '';
  vm.musics = [];
  vm.generos = GENEROS;
  vm.meuGenero = '';
  vm.progressbar = ngProgressFactory.createInstance();

  var mapearSequencia = function(sequencia) {
    return {
      id: sequencia.id,
      nome: sequencia.nome,
      origem: sequencia.origem,
      acordes: sequencia.acordes.map(function(acorde) {
        return { acorde: acorde, cor: COR_ACORDE };
      })
    };
  };

  vm.temAcorde = function(acorde) {
    if (vm.minhaSequencia.acordes) {
      return (vm.minhaSequencia.acordes.indexOf(acorde) > -1);
    } else {
      return false;
    }
  };

  vm.carregarSequencias = function() {
    vm.carregandoCatalogo = true;
    vm.erroCatalogo = '';
    return $http.get('sequencias')
      .success(function(data) {
        vm.sequenciasFamosas = data.map(mapearSequencia);
        vm.carregandoCatalogo = false;
      })
      .error(function() {
        vm.carregandoCatalogo = false;
        vm.erroCatalogo = 'Não foi possível carregar as sequências.';
      });
  };

  vm.carregarAcordes = function() {
    return $http.get('acordes')
      .success(function(data) {
        vm.acordesDisponiveis = data.sort();
      })
      .error(function() {
        vm.erroCadastro = 'Não foi possível carregar os acordes.';
      });
  };

  vm.adicionarAcorde = function() {
    var acorde = (vm.novoAcorde || '').trim();
    if (!acorde) {
      return;
    }
    if (vm.novaSequencia.acordes.length >= 16) {
      vm.erroCadastro = 'Uma sequência pode ter no máximo 16 acordes.';
      return;
    }
    vm.novaSequencia.acordes.push({ acorde: acorde, cor: COR_ACORDE });
    vm.novoAcorde = '';
    vm.erroCadastro = '';
  };

  vm.removerAcorde = function(index) {
    vm.novaSequencia.acordes.splice(index, 1);
  };

  vm.cadastrarSequencia = function() {
    var nome = (vm.novaSequencia.nome || '').trim();
    if (!nome || vm.novaSequencia.acordes.length === 0) {
      vm.erroCadastro = 'Informe o nome e pelo menos um acorde.';
      return;
    }

    vm.salvando = true;
    vm.erroCadastro = '';
    vm.progressbar.start();

    $http.post('sequencias', {
      nome: nome,
      acordes: vm.novaSequencia.acordes.map(function(acorde) {
        return acorde.acorde;
      })
    }).success(function(data) {
      var sequencia = mapearSequencia(data);
      vm.sequenciasFamosas.push(sequencia);
      vm.novaSequencia = { nome: '', acordes: [] };
      vm.novoAcorde = '';
      vm.salvando = false;
      vm.progressbar.complete();
      vm.pesquisarPorSequencia(sequencia);
    }).error(function(data) {
      vm.salvando = false;
      vm.progressbar.complete();
      vm.erroCadastro = (data && data.erro) ? data.erro : 'Não foi possível cadastrar a sequência.';
    });
  };

  vm.pesquisarPorSequencia = function(sequencia) {
    if (sequencia) {
      vm.minhaSequencia = sequencia;
    }
    if (!vm.minhaSequencia || !vm.minhaSequencia.acordes ||
        vm.minhaSequencia.acordes.length === 0) {
      return;
    }

    vm.progressbar.start();
    vm.esfigeSpeech = 'Procurando músicas com base na sequencia...';
    vm.isSearching = true;
    vm.musics = [];

    var searchString = 'similares?sequencia_id=' + encodeURIComponent(vm.minhaSequencia.id);
    if (vm.meuGenero !== '' && vm.meuGenero !== null) {
      searchString += '&generos=' + encodeURIComponent(vm.meuGenero);
    }

    $http.get(searchString)
      .success(function(data) {
        vm.progressbar.complete();
        vm.esfigeSpeech = 'Encontrei essas músicas';
        vm.isSearching = false;
        vm.showSearchResultsCount = true;
        vm.musics = data;
      })
      .error(function() {
        vm.progressbar.complete();
        vm.esfigeSpeech = 'Ops! Algo errado.';
        vm.isSearching = false;
        vm.showSearchResultsCount = false;
      });
  };

  vm.limparPesquisa = function() {
    vm.minhaSequencia = {};
    vm.musics = [];
    vm.showSearchResultsCount = false;
  };

  vm.goToLirics = function(music) {
    $window.open(music.url);
  };

  vm.goToResults = function() {
    vm.showSearchResultsCount = false;
    $("body").animate({scrollTop: $("#results").offset().top}, "slow");
  };

  vm.carregarSequencias();
  vm.carregarAcordes();
});
