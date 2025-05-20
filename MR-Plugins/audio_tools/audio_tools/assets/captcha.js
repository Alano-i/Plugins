async function verifyCaptcha(element,YMtoken,imgUrl, extra) {

    try {
      // 1. 获取图片二进制数据并转为 base64
      const response = await fetch(imgUrl);
      const buffer = await response.arrayBuffer();
      const base64Image = btoa(String.fromCharCode(...new Uint8Array(buffer))); // 转换为 Base64 编码


      // 3. 请求数据
      const url = "http://api.jfbym.com/api/YmServer/customApi";
      const data = {
        token: `${YMtoken}`,
        type: "30109",
        image: base64Image,
        extra: extra
      };

      const headers = {
        "Content-Type": "application/json"
      };

      // 4. 发起 POST 请求 使用 fetch
      var apiResponse = await fetch(url, {
        method: 'POST', // 设置请求方法
        // mode: "no-cors",

        headers: headers, // 设置请求头
        body: JSON.stringify(data), // 将数据转为 JSON 字符串作为请求体

      });

      // 5. 处理响应
      const responseJson =await apiResponse.json();
      console.log(responseJson); // 处理 JSON 响应数据
      switch (String(responseJson.code)) {
        case "10000":
          const pos = responseJson.data.data.split(',');
          clickCaptcha(element,{
            x: pos[0], y: pos[1]
          })
          return {
            x: pos[0], y: pos[1]
          };
        case "10007":
          // 图片未识别成功
          clickCaptcha(element,{
            x: 0, y: 0
          })
          return {
            x: 50, y: 50
          };
        default:
          // 可根据需求处理其他响应情况
          console.error('Unexpected response code:', responseJson.code);
          clickCaptcha(element,{
            x: 0, y: 0
          })
          return {
            x: 0, y: 0
          };
      }

    } catch (error) {
      console.error("Error:", error);
      return {
        x: 0,
        y: 0
      }; // 默认返回值
    }
  }

  // Example usage
  // verifyCaptcha('https://example.com/captcha.jpg', 'someExtraData')
  //     .then(result => console.log(result))
  //     .catch(error => console.error(error));



  function clickCaptcha(element,pos) {
    // alert(pos['x']+","+pos['y'])
    var targetElement = element.querySelector('.yidun_bgimg');

    // 检查元素是否存在
    if (targetElement) {

      // var x =70;  // 元素中间的 x 坐标
      // var y = 73;  // 元素中间的 y 坐标

      var rect = targetElement.getBoundingClientRect();
      var x = rect.left + ~~pos['x']; // 元素中间的 x 坐标
      var y = rect.top + ~~pos['y']; // 元素中间的 y 坐标

      // 创建鼠标点击事件
      var event = new MouseEvent('click', {
        clientX: x, // 鼠标点击的 x 坐标
        clientY: y, // 鼠标点击的 y 坐标
        bubbles: true, // 事件冒泡
        cancelable: true // 事件可取消
      });

      // 触发事件
      targetElement.dispatchEvent(event);
      console.log(`已模拟点击元素: .yidun_bgimg, 坐标: (${x}, ${y})`);
    } else {
      console.log('未找到元素 .yidun_bgimg');
    }
  }



  function verify_captcha(elementId) {


  }

  function createCaptcha(elementId,YMtoken)
  {
    captchas=document.getElementById('captchas')
    captcha=document.createElement('div')
    captcha_ve=document.createElement('div')
    captcha.id=elementId
    captcha_ve.id=elementId+'-ve'
    captcha_ve.innerHTML='ready'
    captchas.appendChild(captcha)
    captchas.appendChild(captcha_ve)

    var captchaIns;
    initNECaptcha({
      element: `#${elementId}`,
      captchaId: '4da3050565514a35a50541b0e1f54538',
      mode: 'embed',
      width: '320px',
      closeEnable: true,
      apiVersion: 2,
      popupStyles: {
        position: 'fixed',
        top: '20%',

      },
      onClose: function () {
        // 弹出关闭结束后将会触发该函数
      },
      onVerify: function (err, data) {
        if (!err) {
          // 验证成功后，调用 close 方法关闭弹框
          //captchaIns.close()
          // TODO: 验证成功后继续进行业务逻辑
          console.log(data)
        //   captchaIns.refresh()
          document.title=data.validate
          captcha=document.getElementById(elementId+'-ve').innerHTML=data.validate

        }else
        {
          document.title='验证失败'
          captcha=document.getElementById(elementId+'-ve').innerHTML='验证失败'

        }
      },
      onReady: function (ins) {

        captcha=document.getElementById(elementId)

        var imgUrl = ""
        var extra = ""
    console.log(captcha)
        var imgElement = captcha.querySelector('.yidun_bg-img');
        if (imgElement) {
          imgUrl = imgElement.src;
          console.log('验证码图片的 URL: ', imgUrl);
        } else {
          console.log('未找到对应的图片元素');
        }
    
        var extElement = captcha.querySelector('.yidun-fallback__tip');
        if (extElement) {
          extra = extElement.innerHTML;
          console.log('验证码描述的 ext: ', extra);
        } else {
          console.log('未找到对应的描述元素');
        }
        verifyCaptcha(captcha,YMtoken,imgUrl, extra)

      }
    }, function (instance) {
      // 初始化成功后得到验证实例 instance，可以调用实例的方法
      captchaIns = instance
      captchaIns.verify()

    }, function (err) {
      // 初始化失败后触发该函数，err 对象描述当前错误信息
    })
  }
  function destroyCaptcha(elementId)
  {
   document.getElementById(elementId).remove()
    document.getElementById(elementId+'-ve').remove()

  }