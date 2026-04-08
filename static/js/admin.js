// small helper to fetch CSRF token
function getCSRF(){ return document.querySelector('[name=csrfmiddlewaretoken]').value; }

// expose for templates
window.getCSRF = getCSRF;
