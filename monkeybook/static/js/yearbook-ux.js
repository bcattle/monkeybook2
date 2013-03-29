function bind_mousewheel_slider_arrows_and_hash() {
    // Mousewheel
//    $('#book-zoom').mousewheel(function(event, delta, deltaX, deltaY) {
//        var data = $(this).data(),
//            step = 30,
//            flipbook = $('.sj-book'),
//            actualPos = $('#slider').slider('value')*step;
//
//        if (typeof(data.scrollX)==='undefined') {
//            data.scrollX = actualPos;
//            data.scrollPage = flipbook.turn('page');
//        }
//
//        data.scrollX = Math.min($( "#slider" ).slider('option', 'max')*step,
//            Math.max(0, data.scrollX + deltaX));
//
//        var actualView = Math.round(data.scrollX/step),
//            page = Math.min(flipbook.turn('pages'), Math.max(1, actualView*2 - 2));
//
//        if ($.inArray(data.scrollPage, flipbook.turn('view', page))==-1) {
//            data.scrollPage = page;
//            flipbook.turn('page', page);
//        }
//
//        if (data.scrollTimer)
//            clearInterval(data.scrollTimer);
//
//        data.scrollTimer = setTimeout(function(){
//            data.scrollX = undefined;
//            data.scrollPage = undefined;
//            data.scrollTimer = undefined;
//        }, 1000);
//    });

    // Slider
//    $("#slider").slider({
//        min: 1,
//        max: 100,
//
//        start: function(event, ui) {
//            if (!window._thumbPreview) {
//                _thumbPreview = $('<div />', {'class': 'thumbnail'}).html('<div></div>');
//                setPreview(ui.value);
//                _thumbPreview.appendTo($(ui.handle));
//            } else
//                setPreview(ui.value);
//            moveBar(false);
//        },
//
//        slide: function(event, ui) {
//            setPreview(ui.value);
//        },
//
//        stop: function() {
//            if (window._thumbPreview)
//                _thumbPreview.removeClass('show');
//
//            $('.sj-book').turn('page', Math.max(1, $(this).slider('value')*2 - 2));
//        }
//    });

    // URIs
    Hash.on('^page\/([0-9]*)$', {
        yep: function(path, parts) {
            var page = parts[1];
            if (page!==undefined) {
                if ($('.sj-book').turn('is'))
                    $('.sj-book').turn('page', page);
            }
        },
        nop: function(path) {
            if ($('.sj-book').turn('is'))
                $('.sj-book').turn('page', 1);
        }
    });

    // Arrows
    $(document).keydown(function(e){
        var previous = 37, next = 39;
        switch (e.keyCode) {
            case previous:
                $('.sj-book').turn('previous');
                break;
            case next:
                $('.sj-book').turn('next');
                break;
        }
    });

}

function zoomHandle(e) {
    if ($('.sj-book').data().zoomIn)
        zoomOut();
    else if (e.target && $(e.target).hasClass('zoom-this')) {
        zoomThis($(e.target));
    }
}

function zoomThis(pic) {
    var	position, translate,
        tmpContainer = $('<div />', {'class': 'zoom-pic'}),
        transitionEnd = $.cssTransitionEnd(),
        tmpPic = $('<img />'),
        zCenterX = $('#book-zoom').width()/2,
        zCenterY = $('#book-zoom').height()/2,
        bookPos = $('#book-zoom').offset(),
        picPos = {
            left: pic.offset().left - bookPos.left,
            top: pic.offset().top - bookPos.top
        },
        completeTransition = function() {
            $('#book-zoom').unbind(transitionEnd);

            if ($('.sj-book').data().zoomIn) {
                tmpContainer.appendTo($('body'));

                $('body').css({'overflow': 'hidden'});

                tmpPic.css({
                    margin: position.top + 'px ' + position.left+'px'
                }).
                    appendTo(tmpContainer).
                    fadeOut(0).
                    fadeIn(500);
            }
        };
    $('.sj-book').data().zoomIn = true;
    $('.sj-book').turn('disable', true);
    $(window).resize(zoomOut);
    tmpContainer.click(zoomOut);

    tmpPic.load(function() {
        var realWidth = $(this)[0].width,
            realHeight = $(this)[0].height,
            zoomFactor = realWidth/pic.width(),
            picPosition = {
                top:  (picPos.top - zCenterY)*zoomFactor + zCenterY + bookPos.top,
                left: (picPos.left - zCenterX)*zoomFactor + zCenterX + bookPos.left
            };

        position = {
            top: ($(window).height()-realHeight)/2,
            left: ($(window).width()-realWidth)/2
        };

        translate = {
            top: position.top-picPosition.top,
            left: position.left-picPosition.left
        };

        $('.samples .bar').css({visibility: 'hidden'});
        $('#slider-bar').hide();

        $('#book-zoom').transform(
            'translate('+translate.left+'px, '+translate.top+'px)' +
                'scale('+zoomFactor+', '+zoomFactor+')');

        if (transitionEnd)
            $('#book-zoom').bind(transitionEnd, completeTransition);
        else
            setTimeout(completeTransition, 1000);

    });
    tmpPic.attr('src', pic.attr('src'));
}

function zoomOut() {
    var transitionEnd = $.cssTransitionEnd(),
        completeTransition = function(e) {
            $('#book-zoom').unbind(transitionEnd);
            $('.sj-book').turn('disable', false);
            $('body').css({'overflow': 'auto'});
            moveBar(false);
        };

    $('.sj-book').data().zoomIn = false;

    $(window).unbind('resize', zoomOut);

    moveBar(true);

    $('.zoom-pic').remove();
    $('#book-zoom').transform('scale(1, 1)');
    $('.samples .bar').css({visibility: 'visible'});
    $('#slider-bar').show();

    if (transitionEnd)
        $('#book-zoom').bind(transitionEnd, completeTransition);
    else
        setTimeout(completeTransition, 1000);
}

//function moveBar(yes) {
//    if (Modernizr && Modernizr.csstransforms) {
//        $('#slider .ui-slider-handle').css({zIndex: yes ? -1 : 10000});
//    }
//}
//
//function setPreview(view) {
//    var previewWidth = 115,
//        previewHeight = 73,
//        previewSrc = 'pages/preview.jpg',
//        preview = $(_thumbPreview.children(':first')),
//        numPages = (view==1 || view==$('#slider').slider('option', 'max')) ? 1 : 2,
//        width = (numPages==1) ? previewWidth/2 : previewWidth;
//
//    _thumbPreview.
//        addClass('no-transition').
//        css({width: width + 15,
//            height: previewHeight + 15,
//            top: -previewHeight - 30,
//            left: ($($('#slider').children(':first')).width() - width - 15)/2
//        });
//
//    preview.css({
//        width: width,
//        height: previewHeight
//    });
//
//    if (preview.css('background-image')==='' || preview.css('background-image')=='none') {
//        preview.css({backgroundImage: 'url(' + previewSrc + ')'});
//        setTimeout(function(){
//            _thumbPreview.removeClass('no-transition');
//        }, 0);
//    }
//
//    preview.css({backgroundPosition:
//        '0px -'+((view-1)*previewHeight)+'px'
//    });
//}
