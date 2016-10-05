angular.module('deciframeApp').controller('SequenciaController', function($http, $window, ngProgressFactory, $anchorScroll, $location, GENEROS) {
  var sequencia1 = {
    'index': 1,
    'acordes': [
      { 'acorde': 'Bm', 'cor': '#2E1C74' },
      { 'acorde': 'G',  'cor': '#2E1C74' },
      { 'acorde': 'D',  'cor': '#2E1C74' },
      { 'acorde': 'A',  'cor': '#2E1C74' }
  ]};
  var sequencia2 = {
    'index': 1,
    'acordes': [
      { 'acorde': 'C',  'cor': '#2E1C74' },
      { 'acorde': 'G',  'cor': '#2E1C74' },
      { 'acorde': 'Am', 'cor': '#2E1C74' },
      { 'acorde': 'F',  'cor': '#2E1C74' }
  ]};
  var sequencia3 = {
    'index': 1,
    'acordes': [
      { 'acorde': 'Gm', 'cor': '#2E1C74' },
      { 'acorde': 'F',  'cor': '#2E1C74' }
  ]};
  var sequencia4 = {
    'index': 1,
    'acordes': [
      { 'acorde': 'C',  'cor': '#2E1C74' },
      { 'acorde': 'C7', 'cor': '#2E1C74' },
      { 'acorde': 'F',  'cor': '#2E1C74' },
      { 'acorde': 'Fm', 'cor': '#2E1C74' }
  ]};
  var vm = this;
  vm.sequenciasFamosas = [];
  vm.sequenciasFamosas.push(sequencia1);
  vm.sequenciasFamosas.push(sequencia2);
  vm.sequenciasFamosas.push(sequencia3);
  vm.sequenciasFamosas.push(sequencia4);
  vm.minhaSequencia = {};
  vm.isSearching = false;
  vm.showSearchResultsCount = false;
  vm.esfigeSpeech =  "";
  vm.musics = [];
  vm.generos = GENEROS;
  vm.meuGenero = "";
  vm.progressbar = ngProgressFactory.createInstance();

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
      vm.minhaSequencia = sequencia;
    }
    vm.progressbar.start();
    vm.esfigeSpeech = "Procurando músicas com base na sequencia...";
    vm.isSearching = true;
    vm.musics = [];

    var apiUrl = "https://ciframe.herokuapp.com/";
    var searchString = "similares?sequencia=".concat(createChordsString(vm.minhaSequencia.acordes));
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
