(function() {
	'use strict';

	angular
		.module('DecifraMe', [
			'ui-router'
			])
		.config(function($stateProvider, $urlRouterProvider) {
            $stateProvider
                .state('home', {
                    url: '/',
                    templateUrl: '/assets/partials/home.html',
                    controller: 'MainCtrl',
                    controllerAs: 'main'
                });

            $urlRouterProvider
                .otherwise('/');
        })
})();