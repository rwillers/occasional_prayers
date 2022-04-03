// Target prayer text
p = document.getElementsByTagName('main')[0];


// Set up and handle gender pronoun toggle
if (p.innerHTML.search(/<em>him<\/em>/i) != -1 || p.innerHTML.search(/<em>his<\/em>/i) != -1 || p.innerHTML.search(/<em>he<\/em>/i) != -1 || p.innerHTML.search(/<em>himself<\/em>/i) != -1 || p.innerHTML.search(/<em>brother<\/em>/i) != -1) {
	// Code ems at page load so that we don't need to know current selection later
	temp = p.innerHTML.replace(/<em>him<\/em>/gi, '<em data-t="obj">him</em>');
	temp = temp.replace(/<em>his<\/em>/gi, '<em data-t="pos">his</em>');
	temp = temp.replace(/<em>he<\/em>/gi, '<em data-t="sub">he</em>');
	temp = temp.replace(/<em>himself<\/em>/gi, '<em data-t="ref">himself</em>');
	temp = temp.replace(/<em>brother<\/em>/gi, '<em data-t="rel">brother</em>');
	p.innerHTML = temp;

	// Make toggle visible
	document.getElementById('pronouns').style.display = 'block';
}

function togglePronouns(g) {
	if (g == 'f') {
		document.getElementById('toggleM').className = '';
		document.getElementById('toggleF').className = 'current';
		temp = p.innerHTML.replace(/<em data-t="obj">[a-z]*<\/em>/gi, '<em data-t="obj">her</em>');
		temp = temp.replace(/<em data-t="pos">[a-z]*<\/em>/gi, '<em data-t="pos">her</em>');
		temp = temp.replace(/<em data-t="sub">[a-z]*<\/em>/gi, '<em data-t="sub">she</em>');
		temp = temp.replace(/<em data-t="ref">[a-z]*<\/em>/gi, '<em data-t="ref">herself</em>');
		temp = temp.replace(/<em data-t="rel">[a-z]*<\/em>/gi, '<em data-t="rel">sister</em>');
	} else if (g == 'm') {
		document.getElementById('toggleF').className = '';
		document.getElementById('toggleM').className = 'current';
		temp = p.innerHTML.replace(/<em data-t="obj">[a-z]*<\/em>/gi, '<em data-t="obj">him</em>');
		temp = temp.replace(/<em data-t="pos">[a-z]*<\/em>/gi, '<em data-t="pos">his</em>');
		temp = temp.replace(/<em data-t="sub">[a-z]*<\/em>/gi, '<em data-t="sub">he</em>');
		temp = temp.replace(/<em data-t="ref">[a-z]*<\/em>/gi, '<em data-t="ref">himself</em>');
		temp = temp.replace(/<em data-t="rel">[a-z]*<\/em>/gi, '<em data-t="rel">brother</em>');
	} else if (g == 'p') {
		temp = p.innerHTML.replace(/<em data-t="obj">[a-z]*<\/em>/gi, '<em data-t="obj">them</em>');
		temp = temp.replace(/<em data-t="pos">[a-z]*<\/em>/gi, '<em data-t="pos">their</em>');
		temp = temp.replace(/<em data-t="sub">[a-z]*<\/em>/gi, '<em data-t="sub">they</em>');
		temp = temp.replace(/<em data-t="ref">[a-z]*<\/em>/gi, '<em data-t="ref">themselves</em>');
		temp = temp.replace(/<em data-t="rel">[a-z]*<\/em>/gi, '<em data-t="rel">siblings</em>');
	}
	p.innerHTML = temp;
}


// Set up name placeholder
if (p.innerHTML.search(/[_]{2,}/i) != -1 || p.innerHTML.search(/<em>N\.<\/em>/) != -1) {
	temp = p.innerHTML.replace(/[_]{2,}/g, '<span class="placeholder">Name</span>');
	temp = temp.replace(/<em>N\.<\/em>/g, '<span class="placeholder">Name</span>');
	p.innerHTML = temp;
}
