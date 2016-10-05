angular.module('deciframeApp').controller('MusicaController', function($http, $window, ngProgressFactory, $anchorScroll, $location, GENEROS) {
  var vm = this;
  vm.acordes = [];
  vm.minhaMusica = {};
  vm.isSearching = false;
  vm.showSearchResultsCount = false;
  vm.esfigeSpeech =  "";
  vm.musics = [];
  vm.generos = GENEROS;
  vm.meuGenero = "";
  vm.progressbar = ngProgressFactory.createInstance();
  var apiUrl = "https://ciframe-api.herokuapp.com/";

  vm.getMusicas = function(val) {
    vm.progressbar.start();
    return $http.get(apiUrl.concat('search?key='+val)).then(function(response) {
      vm.progressbar.complete();
      return response.data;
    });
  };

  vm.addAcorde = function(acorde) {
    if (vm.meusAcordes.indexOf(acorde) == -1) {
      vm.meusAcordes.push(acorde);
    } else {
      var index = vm.meusAcordes.indexOf(acorde);
      if (index > -1) vm.meusAcordes.splice(index, 1);
    }
    vm.pesquisarPorAcordes();
  }
  vm.temAcorde = function(acorde) {
    return (vm.meusAcordes.indexOf(acorde) > -1);
  }

  var createChordsString = function(chords) {
    var str = "";
    for (var i = 0; i < chords.length; i++) {
      str = str.concat(chords[i].acorde, ',');
    }
    return str.substring(0, str.length-1);
  }

  vm.pesquisarPorMusica = function(musica) {
    if (musica) {
      vm.minhaMusica = musica;
    }
    vm.progressbar.start();
    vm.esfigeSpeech = "Procurando músicas similares à "+vm.minhaMusica.nome_musica+" ("+vm.minhaMusica.nome_artista+")"+"...";
    vm.isSearching = true;
    vm.musics = [];

    var searchString = "similares?id_unico_musica=".concat(vm.minhaMusica.id_unico_musica);
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

  vm.goToLirics = function(music) {
    $window.open(music.url);
  };

  vm.goToResults = function() {
    vm.showSearchResultsCount = false;
    $("body").animate({scrollTop: $("#results").offset().top}, "slow");
  };
});
