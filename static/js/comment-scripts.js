var extraData = {root_id: 0, reply_to: 0};

// 发送
$('#comment-form').submit(function () {
    var commentUsername = $("#username").val(),
        commentEmail = $("#email").val(),
        commentWebsite = $("#website").val(),
        commentContent = $("#content").val(),
        articleId = $("#aid").val();
    var data = {id: articleId, username: commentUsername, email: commentEmail, website: commentWebsite, content: commentContent};
    var formData = $.extend({}, data, extraData);
    $.ajax({
        url: "/comment-ajax/",
        type: "POST",
        data: JSON.stringify(formData),
        dataType: "json",
        contentType:"application/json;charset=utf-8",
        success: function (result) {
            if (result['isSuccess'] === true) {
                location.reload(true);
            }
        },
        error: function() {
            alert("抱歉！评论失败！");
        }
    });
    return false
});

//回复
function reply(root_id, reply_to, reply_username) {
    $(".post-comment").appendTo("#message-" + reply_to + ">.comment-content");
    $(".post-comment>.title>.more").css("display", "block");
    $(".post-comment>.title>h3").text("回复：" + reply_username);
    $(".post-comment>form>button").text("发表回复");
    extraData.root_id = root_id;
    extraData.reply_to = reply_to;
    $('html,body').animate({
        'scrollTop': $('.post-comment').offset().top - jQuery(window).height()/4
    }, 500)
}

function cancelReply() {
    $(".post-comment").prependTo(".comment-box");
    $(".post-comment>.title>.more").css("display", "none");
    $(".post-comment>.title>h3").text("发表评论");
    $(".post-comment>form>button").text("发表评论");
    extraData.root_id = 0;
    extraData.reply_to = 0;
}
