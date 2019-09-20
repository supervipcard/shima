/**

 @Name：layuiAdmin 用户登入和注册等
 @Author：贤心
 @Site：http://www.layui.com/admin/
 @License: LPPL

 */

layui.define('form', function(exports){
  var $ = layui.$
  ,layer = layui.layer
  ,laytpl = layui.laytpl
  ,setter = layui.setter
  ,view = layui.view
  ,admin = layui.admin
  ,form = layui.form;

  var $body = $('body');

  //自定义验证
  form.verify({
    nickname: function(value, item){ //value：表单的值、item：表单的DOM对象
      if(!new RegExp("^[a-zA-Z0-9_\u4e00-\u9fa5\\s·]+$").test(value)){
        return '用户名不能有特殊字符';
      }
      if(/(^\_)|(\__)|(\_+$)/.test(value)){
        return '用户名首尾不能出现下划线\'_\'';
      }
      if(/^\d+\d+\d$/.test(value)){
        return '用户名不能全为数字';
      }
    }

    //我们既支持上述函数式的方式，也支持下述数组的形式
    //数组的两个值分别代表：[正则匹配、匹配不符时的提示文字]
    ,pass: [
      /^[\S]{6,12}$/
      ,'密码必须6到12位，且不能出现空格'
    ]
  });


  //发送短信验证码
  admin.sendAuthCode({
    elem: '#LAY-user-getsmscode'
    ,elemPhone: '#LAY-user-login-cellphone'
    ,elemVercode: '#LAY-user-login-vercode'
    ,ajax: {
      url: '/sendsms/' //实际使用请改成服务端真实接口
      ,type: "POST"
      ,dataType: "json"
      ,contentType: "application/json;charset=utf-8"
      ,beforeSend: function(xhr, settings) {
          xhr.setRequestHeader("X-CSRFToken", $('[name="csrfmiddlewaretoken"]').val());
      }
    }
  });




  //更换图形验证码
  $body.on('click', '#LAY-user-get-vercode', function(){
    var othis = $(this);
    var src = othis.attr('src');
    if (src.indexOf("random") == -1) {
      this.src = othis.attr('src') + '&random=' + new Date().getTime()
    }
    else {
      this.src = othis.attr('src').replace(/random=(\d+)/, 'random=' + new Date().getTime())
    }
  });

  //对外暴露的接口
  exports('user', {});
});
