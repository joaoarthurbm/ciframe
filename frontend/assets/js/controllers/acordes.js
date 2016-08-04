angular.module('deciframeApp').controller('AcordesController', function($http, $window, ngProgressFactory, $anchorScroll, $location, GENEROS) {
  var acordesC = [
    { 'acorde': 'C',  'cor': '#e6b300' },
    { 'acorde': 'C#', 'cor': '#e6b300' },
    { 'acorde': 'Cm', 'cor': '#efcc59' },
    { 'acorde': 'C#m','cor': '#efcc59' },
    { 'acorde': 'C7', 'cor': '#d6a602' },
    { 'acorde': 'C#7','cor': '#d6a602' }];
  var acordesD = [
    { 'acorde': 'D',  'cor': '#cb6018' },
    { 'acorde': 'D#', 'cor': '#cb6018' },
    { 'acorde': 'Dm', 'cor': '#cf6f3e' },
    { 'acorde': 'D#m','cor': '#cf6f3e' },
    { 'acorde': 'D7', 'cor': '#bc5a1d' },
    { 'acorde': 'D#7','cor': '#bc5a1d' }];
  var acordesE = [
    { 'acorde': 'E',  'cor': '#b72c52' },
    { 'acorde': 'Em', 'cor': '#c5516e' },
    { 'acorde': 'E7', 'cor': '#a92f4d' }];
  var acordesF = [
    { 'acorde': 'F',  'cor': '#ba007c' },
    { 'acorde': 'F#', 'cor': '#ba007c' },
    { 'acorde': 'Fm', 'cor': '#c02a88' },
    { 'acorde': 'F#m','cor': '#c02a88' },
    { 'acorde': 'F7', 'cor': '#ad0076' },
    { 'acorde': 'F#7','cor': '#ad0076' }];
  var acordesG = [
    { 'acorde': 'G',  'cor': '#7b057e' },
    { 'acorde': 'G#', 'cor': '#7b057e' },
    { 'acorde': 'Gm', 'cor': '#882888' },
    { 'acorde': 'G#m','cor': '#882888' },
    { 'acorde': 'G7', 'cor': '#710c77' },
    { 'acorde': 'G#7','cor': '#710c77' }];
  var acordesA = [
    { 'acorde': 'A',  'cor': '#76aadb' },
    { 'acorde': 'A#', 'cor': '#76aadb' },
    { 'acorde': 'Am', 'cor': '#89c0e9' },
    { 'acorde': 'A#m','cor': '#89c0e9' },
    { 'acorde': 'A7', 'cor': '#6c9ecc' },
    { 'acorde': 'A#7','cor': '#6c9ecc' }];
  var acordesB = [
    { 'acorde': 'B',  'cor': '#a3bd31' },
    { 'acorde': 'Bm', 'cor': '#cdd54f' },
    { 'acorde': 'B7', 'cor': '#96b02f' }];
  var vm = this;
  vm.acordes = [];
  vm.acordes.push(acordesC);
  vm.acordes.push(acordesD);
  vm.acordes.push(acordesE);
  vm.acordes.push(acordesF);
  vm.acordes.push(acordesG);
  vm.acordes.push(acordesA);
  vm.acordes.push(acordesB);
  vm.meusAcordes = [];
  vm.isSearching = false;
  vm.esfigeSpeech =  "";
  vm.musics = [];
  vm.generos = GENEROS;
  vm.meuGenero = "";
  vm.progressbar = ngProgressFactory.createInstance();

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

  vm.pesquisarPorAcordes = function() {
    if (vm.meusAcordes.length) {
      vm.progressbar.start();
      vm.esfigeSpeech = "Procurando músicas com base nos acordes...";
      vm.isSearching = true;

      var apiUrl = "http://127.0.0.1:5000/";
      var searchString = "similares?acordes=".concat(createChordsString(vm.meusAcordes));
      if (vm.meuGenero !== "" && vm.meuGenero !== null) {
        searchString += "&generos="+vm.meuGenero;
      }
      console.log("["+vm.meuGenero+"]");
      $http.get(apiUrl.concat(searchString))
        .success(function(data) {
          vm.progressbar.complete();
          vm.esfigeSpeech = "Encontrei essas músicas";
          vm.isSearching = false;
          vm.musics = data;
        })
        .error(function(data) {
          vm.esfigeSpeech = "Ops! Algo errado.";
          vm.isSearching = false;
        });
    } else {
      vm.musics = [];
      vm.esfigeSpeech = "";
      vm.isSearching = false;
    }
  }

  vm.goToLirics = function(music) {
    $window.open(music.url);
  };

  vm.goToResults = function() {
    $("body").animate({scrollTop: $("#results").offset().top}, "slow");
  };
});
