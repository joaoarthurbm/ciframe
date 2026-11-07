angular.module('deciframeApp').controller('SequenciaController', function($http, $window, ngProgressFactory, $anchorScroll, $location, GENEROS) {
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
  vm.novaSequencia = "";
  vm.cadastrando = false;
  vm.mensagemCadastro = "";
  vm.mensagemCatalogo = "";

  var apiUrl = "";

  vm.carregarSequencias = function() {
    $http.get(apiUrl.concat('sequencias'))
      .success(function(data) {
        vm.mensagemCatalogo = "";
        vm.sequenciasFamosas = [];
        if (data) {
          for (var i = 0; i < data.length; i++) {
            var seq = data[i];
            var acordesArr = [];
            if (seq.chords) {
              for (var j = 0; j < seq.chords.length; j++) {
                acordesArr.push({ 'acorde': seq.chords[j], 'cor': '#2E1C74' });
              }
            }
            vm.sequenciasFamosas.push({
              'index': i + 1,
              'acordes': acordesArr,
              'chords_key': seq.chords_key || '',
              'origem': seq.origem || 'custom',
              'rawChords': seq.chords || []
            });
          }
        }
      })
      .error(function(data) {
        vm.mensagemCatalogo = "Não foi possível carregar o catálogo de sequências.";
      });
  };

  vm.carregarSequencias();

  vm.temAcorde = function(acorde) {
    if (vm.minhaSequencia.acordes) {
      return (vm.minhaSequencia.acordes.indexOf(acorde) > -1);
    } else {
      return false;
    }
  }

  var createChordsString = function(chords) {
    var str = "";
    for (var i = 0; i < chords.length; i++) {
      str = str.concat(chords[i].acorde, ',');
    }
    return str.substring(0, str.length-1);
  }

  vm.pesquisarPorSequencia = function(sequencia) {
    if (sequencia) {
      // normalize to format expected
      vm.minhaSequencia = {
        acordes: sequencia.acordes || []
      };
      if (sequencia.rawChords && sequencia.rawChords.length > 0) {
        // store raw for search
        vm._ultimaSequenciaRaw = sequencia.rawChords;
      } else if (sequencia.chords_key) {
        vm._ultimaSequenciaRaw = createChordsString(sequencia.acordes).split(',');
      } else {
        vm._ultimaSequenciaRaw = createChordsString(sequencia.acordes).split(',');
      }
    }
    vm.progressbar.start();
    vm.esfigeSpeech = "Procurando músicas com base na sequencia...";
    vm.isSearching = true;
    vm.musics = [];

    var searchString = "";
    if (vm._ultimaSequenciaRaw && vm._ultimaSequenciaRaw.length > 0) {
      // use comma joined form
      var s = "";
      for (var i = 0; i < vm._ultimaSequenciaRaw.length; i++) {
        s = s.concat(vm._ultimaSequenciaRaw[i], ',');
      }
      searchString = "similares?sequencia=".concat(s.substring(0, s.length-1));
    } else {
      searchString = "similares?sequencia=".concat(createChordsString(vm.minhaSequencia.acordes));
    }
    if (vm.meuGenero !== "" && vm.meuGenero !== null) {
      searchString += "&generos="+vm.meuGenero;
    }
    $http.get(apiUrl.concat(searchString))
      .success(function(data) {
        vm.progressbar.complete();
        vm.esfigeSpeech = "Encontrei essas músicas";
        vm.isSearching = false;
        vm.showSearchResultsCount = true;
        vm.musics = data;
      })
      .error(function(data) {
        vm.esfigeSpeech = "Ops! Algo errado.";
        vm.isSearching = false;
        vm.showSearchResultsCount = false;
      });
  }

  vm.cadastrarSequencia = function() {
    if (!vm.novaSequencia || vm.novaSequencia.trim() === '') {
      vm.mensagemCadastro = "Informe os acordes separados por vírgula";
      return;
    }
    vm.cadastrando = true;
    vm.mensagemCadastro = "";
    var parts = vm.novaSequencia.split(',');
    var chords = [];
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i].trim();
      if (p !== '') chords.push(p);
    }
    if (chords.length === 0) {
      vm.cadastrando = false;
      vm.mensagemCadastro = "Informe os acordes separados por vírgula";
      return;
    }
    $http.post(apiUrl.concat('sequencias'), { chords: chords })
      .success(function(data) {
        vm.cadastrando = false;
        if (data && data.duplicado) {
          vm.mensagemCadastro = "Sequência já cadastrada";
        } else {
          vm.mensagemCadastro = "Sequência cadastrada com sucesso";
        }
        vm.novaSequencia = "";
        vm.carregarSequencias();
      })
      .error(function(data) {
        vm.cadastrando = false;
        vm.mensagemCadastro = "Erro ao cadastrar";
      });
  }

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
});
