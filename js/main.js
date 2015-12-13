(function() {
    'use strict';

    angular
        .module('DecifraMe')
        .controller('MainCtrl', function($scope, $http, $window) {

          $scope.filtroArtista = ["Molejo"];
          $scope.filtroEstilo = ["MPB"];
          $scope.filtroFacilidade = [70, 100];
          $scope.tituloMusica = "Vou voltar pra sacanagem";

          $scope.musicas = [];
          $scope.meusAcordes = [];

          $scope.pesquisarPorNome = function() {
            console.log("enrouuurgurbsbsfyivsbsybvv");
            $http.get("http://localhost:5000/busca?musica=" + $scope.tituloMusica)
              .success(function(data, headers) {
                musicas = data;
                console.log("Aheeeee");
              })
              .error(function(data, headers) {
                console.log("Erro ao tentar pesquisar por nome!");
              });
          }

          $scope.pesquisarPorAcordes = function() {
            $http.get(
              "http://localhost:5000/rankByAcordes?acordes=" + $scope.meusAcordes +
                "&filtro-generos=" + $scope.filtroEstilo +
                "&filtro-artistas=" + $scope.filtroArtista +
                "&min=" + $scope.filtroFacilidade[0] +
                "&max=" + $scope.filtroFacilidade[1]
              )
                .success(function (data, headers) {
                  musicas = data;
                })
                .error(function () {
                  console.log("Erro ao tentar pesquisar por acordes!");
                })
          }
        })
})();
