function addPage(page, book) {
    var id, pages = book.turn('pages');
    if (!book.turn('hasPage', page)) {
        var element = $('<div />',
            {'class': 'own-size',
                css: {width: 456, height: 333}
            }).
            html('<div class="loader"></div>');

        if (book.turn('addPage', element, page)) {
            getPage(page);         // Defined in addpage-files.js or addpage-api.js
        }
    }
}

function loadApp() {
    var flipbook = $('.sj-book');

    // Hook up left and right buttons
    $('.next-button').click(function(){ flipbook.turn('next'); });
    $('.previous-button').click(function(){ flipbook.turn('previous'); });

    // Check if the CSS was already loaded
    if (flipbook.width()==0 || flipbook.height()==0) {
        setTimeout(loadApp, 10);
        return;
    }

    // yearbook-ux.js
    bind_mousewheel_slider_arrows_and_hash();

    // Flipbook
    flipbook.bind(($.isTouch) ? 'touchend' : 'click', zoomHandle);
    flipbook.turn({
        elevation: 50,
        acceleration: !isChrome(),
        autoCenter: true,
        gradients: true,
        duration: 1000,
        pages: 32,
        when: {
            turning: function(e, page, view) {
                var book = $(this),
                    currentPage = book.turn('page'),
                    pages = book.turn('pages');

                if (currentPage>3 && currentPage<pages-3) {
                    if (page==1) {
                        book.turn('page', 2).turn('stop').turn('page', page);
                        e.preventDefault();
                        return;
                    } else if (page==pages) {
                        book.turn('page', pages-1).turn('stop').turn('page', page);
                        e.preventDefault();
                        return;
                    }
                } else if (page>3 && page<pages-3) {
                    if (currentPage==1) {
                        book.turn('page', 2).turn('stop').turn('page', page);
                        e.preventDefault();
                        return;
                    } else if (currentPage==pages) {
                        book.turn('page', pages-1).turn('stop').turn('page', page);
                        e.preventDefault();
                        return;
                    }
                }

                updateDepth(book, page);

                if (page>=2)
                    $('.sj-book .p2').addClass('fixed');
                else
                    $('.sj-book .p2').removeClass('fixed');

                if (page<book.turn('pages'))
                    $('.sj-book .p31').addClass('fixed');
                else
                    $('.sj-book .p31').removeClass('fixed');

                Hash.go('page/'+page).update();
            },

            turned: function(e, page, view) {
                var book = $(this);
                if (page==2 || page==3) {
                    book.turn('peel', 'br');
                }
                updateDepth(book);
//                $('#slider').slider('value', getViewNumber(book, page));
                book.turn('center');
            },

            start: function(e, pageObj) {
//                moveBar(true);
            },

            end: function(e, pageObj) {
                var book = $(this);
                updateDepth(book);

                setTimeout(function() {
                    $('#slider').slider('value', getViewNumber(book));
                }, 1);

//                moveBar(false);
            },

            missing: function (e, pages) {
                for (var i = 0; i < pages.length; i++)
                    addPage(pages[i], $(this));
            }
        }
    });

//    $('#slider').slider('option', 'max', numberOfViews(flipbook));

    flipbook.addClass('animated');

    // Show canvas
    $('#canvas').css({visibility: ''});
}

// Other (possibly helpful) functions

function updateDepth(book, newPage) {
	var page = book.turn('page'),
		pages = book.turn('pages'),
		depthWidth = 16*Math.min(1, page*2/pages);

    newPage = newPage || page;
	if (newPage>3)
		$('.sj-book .p2 .depth').css({
			width: depthWidth,
			left: 20 - depthWidth
		});
	else
		$('.sj-book .p2 .depth').css({width: 0});

    depthWidth = 16*Math.min(1, (pages-page)*2/pages);

	if (newPage<pages-3)
		$('.sj-book .p31 .depth').css({
			width: depthWidth,
			right: 20 - depthWidth
		});
	else
		$('.sj-book .p31 .depth').css({width: 0});
}

function numberOfViews(book) {
	return book.turn('pages') / 2 + 1;
}

function getViewNumber(book, page) {
	return parseInt((page || book.turn('page'))/2 + 1, 10);
}

function isChrome() {
	// Chrome's unsolved bug
	// http://code.google.com/p/chromium/issues/detail?id=128488
	return navigator.userAgent.indexOf('Chrome')!=-1;
}
