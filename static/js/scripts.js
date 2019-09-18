// 网页加载进度条
// NProgress.start();
// setTimeout(function () {
//     NProgress.done();
// }, 1000);

// 禁止拖动
(function () {
    $('img').attr('draggable', 'false');
    $('a').attr('draggable', 'false');
})();

// 页面回到顶部
$("#gotop").hide();
$(window).scroll(function () {
    if ($(window).scrollTop() > 100) {
        $("#gotop").fadeIn()
    } else {
        $("#gotop").fadeOut()
    }
});
$("#gotop").click(function () {
    $('html,body').animate({
        'scrollTop': 0
    }, 500)
});

// 页面文字是否能被选中
// document.body.onselectstart = document.body.ondrag = function () {
//     return true
// };

// 分页
$('[data-toggle="tooltip"]').tooltip();
jQuery.ias({
    history: false,
    container: '.content',
    item: '.excerpt',
    pagination: '.pagination',
    next: '.next-page a',
    trigger: '查看更多',
    loader: '<div class="pagination-loading"><img src="/static/images/loading.gif" alt=""/></div>',
    triggerPageThreshold: 0,
    onRenderComplete: function () {
        $('.excerpt img').attr('draggable', 'false');
        $('.excerpt a').attr('draggable', 'false')
    }
});

// sidebar浮动
$(window).scroll(function () {
    var aside = $('.aside');
    var asideHeight = aside.height();
    var windowScrollTop = $(window).scrollTop();
    if (windowScrollTop > asideHeight + 60 && aside.length) {
        $('.fixed').css({
            'position': 'fixed',
            'top': '10px',
            'width': '360px'
        })
    } else {
        $('.fixed').removeAttr("style")
    }
});

// 分享
$(".article-share").click(function() {
    $(".share-group").fadeToggle("slow");
});

// 点赞
$('.article-praise').click(function(){
    var id = $(this).data("id");
    var cookie = $.cookie('praise_' + id);
    if (cookie === undefined) {
        alert("感谢您的点赞！");
        $.cookie('praise_' + id, id, {expires: 7});
        $(this).addClass('active');
        $.ajax({
            url: "/praise-ajax/",
            type:"POST",
            data: {id: id},
            dataType: "json",
            success: function(result){

            },
            error: function(){

            }
        });
        return false
    }
    else {
        alert("已经点过赞啦！");
    }
});
