angular.module('deciframeApp').controller('AcordesController', function($scope, $http) {
  $scope.acordesMaiores = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  $scope.acordesMenores = ["Cm", "C#m", "Dm", "D#m", "Em", "Fm", "F#m", "Gm", "G#m", "Am", "A#m", "Bm"];
  $scope.acordesComSetima = ["C7", "C#7", "D7", "D#7", "E7", "F7", "F#7", "G7", "G#7", "A7", "A#7", "B7"];
  $scope.meusAcordes = [];
  $scope.isSearching = false;
  $scope.musicas = [];

  $scope.addAcorde = function(acorde) {
    if ($scope.meusAcordes.indexOf(acorde) == -1) {
      $scope.meusAcordes.push(acorde);
    } else {
      var index = $scope.meusAcordes.indexOf(acorde);
      if (index > -1) $scope.meusAcordes.splice(index, 1);
    }
  }
  $scope.temAcorde = function(acorde) {
    return ($scope.meusAcordes.indexOf(acorde) > -1);
  }
  $scope.pesquisarPorAcordes = function() {
    $scope.isSearching = true;
    // Developing only >>>
    $scope.musicas.push(
      {
        "titulo": "Californication "+$scope.musicas.length,
        "artista": "Red Hot Chili Peppers",
        "link": "http://www.cifraclub.com.br/red-hot-chili-peppers/californication/"
      }
    );
    // Remove later <<<<
    $http.get("")
    .success(function(data) {
      // $scope.musicas = data;
      $scope.isSearching = false;
    })
    .error(function(data) {
      $scope.isSearching = false;
    });
  }
});
