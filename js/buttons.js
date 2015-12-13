(function(){

	var button = document.getElementById('cn-button'),
    wrapper = document.getElementById('cn-wrapper');

    //open and close menu when the button is clicked
	var open = false;
	button.addEventListener('click', handler, false);

	function handler(){
	  if(!open){
	    this.innerHTML = "Fechar";
	    classie.add(wrapper, 'opened-nav');
	  }
	  else{
	    this.innerHTML = "Maiores";
		classie.remove(wrapper, 'opened-nav');
	  }
	  open = !open;
	}
	function closeWrapper(){
		classie.remove(wrapper, 'opened-nav');
	}

	var button2 = document.getElementById('cn-button-2'),
    wrapper2 = document.getElementById('cn-wrapper-2');

    //open and close menu when the button is clicked
	var open2 = false;
	button2.addEventListener('click', handler2, false);

	function handler2(){
	  if(!open2){
	    this.innerHTML = "Fechar";
	    classie.add(wrapper2, 'opened-nav');
	  }
	  else{
	    this.innerHTML = "Menores";
		classie.remove(wrapper2, 'opened-nav');
	  }
	  open2 = !open2;
	}
	function closeWrapper2(){
		classie.remove(wrapper2, 'opened-nav');
	}

})();
