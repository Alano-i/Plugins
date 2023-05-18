// ==UserScript==
// @name           豆瓣资源下载大师：疯子魔改版2023.5.17-1355
// @description    【装这一个脚本就够了！可能是你遇到的最好的豆瓣增强脚本】聚合数百家资源网站，通过右侧边栏1秒告诉你哪些网站能下载豆瓣页面上的电影|电视剧|纪录片|综艺|动画|音乐|图书等，有资源的网站显示绿色，没资源的网站显示黄色，就这么直观！所有豆瓣条目均提供在线播放|阅读、字幕|歌词下载及PT|NZB|BT|磁力|百度盘|115网盘等下载链接，加入官网打死也不出的豆列搜索功能，此外还能给豆瓣条目额外添加IMDB评分|IMDB TOP 250|Metascore评分|烂番茄评分|AniDB评分|Bgm评分|MAL|亚马逊评分等更多评分形式。官方电报群：@doubandown
// @author         白鸽男孩
// @contributor    Rhilip
// @connect        *
// @grant          GM_xmlhttpRequest
// @grant          GM_setClipboard
// @grant          GM_addStyle
// @grant          GM_setValue
// @grant          GM_getValue
// @grant          GM_listValues
// @grant          GM_deleteValue
// @grant          GM_registerMenuCommand
// @require        https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js
// @require        https://greasyfork.org/scripts/368137-encodeToGb2312/code/encodeToGb2312.js?version=601683
// @include        https://movie.douban.com/*
// @include        https://music.douban.com/*
// @include        https://book.douban.com/*
// @include        https://bangumi.moe/search/title*
// @include        https://desitorrents.tv/*
// @include        https://v.dsb.ink/*
// @include        http://www.x5v.net/*
// @license        Zlib/Libpng License
// @version        8.2.9
// @icon           https://img3.doubanio.com/favicon.ico
// @run-at         document-end
// @namespace      doveboy_js
// ==/UserScript==

/* global $, jQuery, encodeToGb2312 */

// This Userscirpt can't run under Greasemonkey 4.x platform
if (typeof GM_xmlhttpRequest === "undefined") {
    alert("不支持Greasemonkey 4.x，请换用暴力猴或Tampermonkey");
    return;
}

// 不属于豆瓣的页面
if (!/douban.com/.test(location.host)) {
    function AutoSearch(host, zInputSelector, btnSelector, dict) {
        if (location.host === host) {
            let match = location.href.match(/#search_(.+)/); // 从url的hash部分获取搜索关键词
            if (match) {
                history.pushState("", document.title, window.location.pathname + window.location.search); // 清空hash
                window.addEventListener("load", function () { // 等待页面完全加载完成
                    let zInput = $(zInputSelector);
                    zInput.val(decodeURIComponent(match[1])); // 填入搜索值
                    dict = $.extend({}, dict);
                    if (dict.ang) { // 补加Event，防止Angular绑定失效。 From: https://stackoverflow.com/questions/34360739/automate-form-submission-on-an-angularjs-website-using-tampermonkey
                        let changeEvent = document.createEvent("HTMLEvents");
                        changeEvent.initEvent("change", true, true);
                        zInput[0].dispatchEvent(changeEvent);
                    }
                    if (dict.notarget) { // 取消form的提交跳转
                        $(btnSelector).parents("form").attr("target", "_self");
                    }
                    $(btnSelector).click(); // 模拟点击
                });
            }
        }
    }

    AutoSearch("bangumi.moe", '#filter-tag-list div.torrent-title-search > md-input-group > input', '#filter-tag-list > div.torrent-search > div:nth-child(3) > button:nth-child(4)', { ang: true });
    AutoSearch("v.dsb.ink", '.search__input', '.icon-search', {});
    AutoSearch("www.x5v.net", '#searchText', '#btnSearch', {});
    AutoSearch("desitorrents.tv", 'input.search_string_input', 'input.search_string_input+img', {});

    return; // 终止脚本运行，防止豆瓣的css以及js片段等污染页面
}

// 阻止其他豆瓣同类脚本加载
var seBwhA = document.createElement("a");
seBwhA.id = "seBwhA";
document.getElementsByTagName("html")[0].appendChild(seBwhA);

// 注入脚本相关的CSS，包括：隐藏、调整豆瓣原先的元素，脚本页面样式
GM_addStyle(`
.c-aside{margin-bottom:30px}.c-aside-body a{border-radius:6px;color:#37a;display:inline-block;letter-spacing:normal;margin:0 8px 8px 0;padding:0 8px;text-align:center;width:65px}.c-aside-body a:link,.c-aside-body a:visited{background-color:#f5f5f5;color:#37a}.c-aside-body a:active,.c-aside-body a:hover{background-color:#e8e8e8;color:#37a}.c-aside-body a.available{background-color:#5ccccc;color:#006363}.c-aside-body a.available:active,.c-aside-body a.available:hover{background-color:#3cc}.c-aside-body a.sites_r0{text-decoration:line-through}
#c_dialog li{margin:10px}#c_dialog{text-align:center}
#interest_sectl .rating_imdb{border-top:1px solid #eaeaea;border-bottom:1px solid #eaeaea;padding-bottom:0}#interest_sectl .rating_wrap{padding-top:15px}#interest_sectl .rating_more{border-bottom:1px solid #eaeaea;color:#9b9b9b;margin:0;padding:15px 0;position:relative}#interest_sectl .rating_more a{left:80px;position:absolute}#interest_sectl .rating_more .titleOverviewSprite{background:url(https://coding.net/u/Changhw/p/MyDoubanMovieHelper/git/raw/master/title_overview_sprite.png) no-repeat;display:inline-block;vertical-align:middle}#interest_sectl .rating_more .popularityImageUp{background-position:-14px -478px;height:8px;width:8px}#interest_sectl .rating_more .popularityImageDown{background-position:-34px -478px;height:8px;width:8px}#interest_sectl .rating_more .popularityUpOrFlat{color:#83c40b}#interest_sectl .rating_more .popularityDown{color:#930e02}
.more{display:block;height:34px;line-height:34px;text-align:center;font-size:14px;background:#f7f7f7}
div#drdm_setting input[type=checkbox]{display:none}div#drdm_setting input[type=checkbox]+label{display:inline-block;width:40px;height:20px;position:relative;transition:.3s;margin:0 20px;box-sizing:border-box;background:#ddd;border-radius:20px;box-shadow:1px 1px 3px #aaa}div#drdm_setting input[type=checkbox]+label:after,div#drdm_setting input[type=checkbox]+label:before{content:'';display:block;position:absolute;left:0;top:0;width:20px;height:20px;transition:.3s;cursor:pointer}div#drdm_setting input[type=checkbox]+label:after{background:#fff;border-radius:50%;box-shadow:1px 1px 3px #aaa}div#drdm_setting input[type=checkbox]:checked+label{background:#aedcae}div#drdm_setting input[type=checkbox]:checked+label:after{background:#5cb85c;left:calc(100% - 20px)}
.top250{background:url(https://s.doubanio.com/f/movie/f8a7b5e23d00edee6b42c6424989ce6683aa2fff/pics/movie/top250_bg.png) no-repeat;width:150px;margin-right:5px;font:12px Helvetica,Arial,sans-serif;margin:5px 0;color:#744900}.top250 span{display:inline-block;text-align:center;height:18px;line-height:18px}.top250 a,.top250 a:active,.top250 a:hover,.top250 a:link,.top250 a:visited{color:#744900;text-decoration:none;background:0}.top250-no{width:34%}.top250-link{width:66%}
.drdm-dl-horizontal dt{float:left;width:160px;overflow:hidden;clear:left;text-align:right;text-overflow:ellipsis;white-space:nowrap}.drdm-dl-horizontal dd{margin-left:180px}
`);

if (GM_getValue('enable_extra_stylesheet', true)) {
    GM_addStyle('#dale_movie_chart_top_right,#dale_movie_home_bottom_right,#dale_movie_home_bottom_right_down,#dale_movie_home_download_bottom,#dale_movie_home_inner_bottom,#dale_movie_home_side_top,#dale_movie_home_top_right,#dale_movie_subject_bottom_super_banner,#dale_movie_subject_download_middle,#dale_movie_subject_inner_middle,#dale_movie_subject_middle_right,#dale_movie_subject_top_midle,#dale_movie_subject_top_right,#dale_movie_tags_top_right,#dale_movie_towhome_explore_right,#dale_review_best_top_right,#footer,#movie_home_left_bottom,.extra,.mobile-app-entrance.block5.app-movie,.qrcode-app,.top-nav-doubanapp,div.gray_ad,div.ticket{display:none}');
}

// -- 定义基础方法 --

// 对使用GM_xmlhttpRequest返回的html文本进行处理并返回DOM树
function page_parser(responseText) {
    // 替换一些信息防止图片和页面脚本的加载，同时可能加快页面解析速度
    // responseText = responseText.replace(/s+src=/ig, ' data-src='); // 图片，部分外源脚本
    // responseText = responseText.replace(/<script[^>]*?>[\S\s]*?<\/script>/ig, ''); //页面脚本
    return (new DOMParser()).parseFromString(responseText, 'text/html');
}

function getDoc(url, meta, callback) {
    GM_xmlhttpRequest({
        method: 'GET',
        url: url,
        onload: function (responseDetail) {
            if (responseDetail.status === 200) {
                let doc = page_parser(responseDetail.responseText);
                callback(doc, responseDetail, meta);
            }
        }
    });
}

function getJSON(url, callback) {
    GM_xmlhttpRequest({
        method: 'GET',
        url: url,
        headers: {
            'Accept': 'application/json'
        },
        onload: function (response) {
            if (response.status >= 200 && response.status < 400) {
                callback(JSON.parse(response.responseText), url);
            } else {
                callback(false, url);
            }
        }
    });
}

// 缓存相关方法
function CacheStorage(name, expire = null) {
    let now = Date.now();
    let cache_name = "drdm_cache_" + (name ? name : 'default');

    if (localStorage[cache_name + "_exp"]) {
        if (now > localStorage[cache_name + "_exp"]) {
            localStorage.removeItem(cache_name);
        }
    }

    let cache = localStorage[cache_name] ? JSON.parse(localStorage[cache_name]) : {};
    localStorage.setItem(cache_name + "_exp", now + expire);

    return {
        flush: function () {
            localStorage.setItem(cache_name, JSON.stringify(cache));
        },

        add: function (name, value) {
            cache[name] = value;
            this.flush();
        },

        del: function (name) {
            if (name) {
                delete cache[name];
                this.flush;
            } else {
                localStorage.removeItem(cache_name);
            }
        },

        get: function (name, def = null) {
            if (name) {
                return cache[name] ? cache[name] : def;
            } else {
                return cache;
            }
        }
    }
}

function clearExpiredCacheValue(force) {
    let StorageKey = [];
    for (let i = 0, len = localStorage.length; i < len; ++i) { // 先从里面取出所有的key
        StorageKey.push(localStorage.key(i));
    }

    let CacheKey = StorageKey.filter(function (x) {
        return x && x.match(/(drdm_cache_.+)_exp/);
    }); // 再从中提取出本脚本缓存的键值

    for (let i = 0,len = CacheKey.length ; i < len ; ++i) {
        let key_name = CacheKey[i];
        let exp_at = localStorage.getItem(key_name);
        if (force || exp_at < Date.now()) {
            localStorage.removeItem(key_name);
            localStorage.removeItem(key_name.slice(0,-4)); // 移除 _exp 后缀
        }
    }
}

let _version = GM_getValue("version", "轻量版");
let delete_site_prefix = "delete_site_";

if (typeof GM_registerMenuCommand !== "undefined") {

    function changeVersionConfirm() {
        if (confirm(`你当前版本是 ${_version}，是否进行切换？`)) {
            GM_setValue("version", _version === "完整版" ? "轻量版" : "完整版");
        }
    }
    GM_registerMenuCommand("脚本功能切换", changeVersionConfirm);

    function changeTagBColor() {
        let now_bcolor_list = [GM_getValue("tag_bcolor_exist", "#00FF00"), GM_getValue("tag_bcolor_not_exist", "#FF0000"), GM_getValue("tag_bcolor_need_login", "#0000FF"), GM_getValue("tag_bcolor_error", "#FFFF00")];
        let name = prompt("请依次输入代表'资源存在','资源不存在','站点需要登陆','站点解析错误'颜色的Hex值，并用英文逗号分割。当前值为：", `${now_bcolor_list.join(',')}`);
        if (name != null && name !== "") {
            try {
                let bcolor_list = name.split(",");
                GM_setValue("tag_bcolor_exist", bcolor_list[0] || "#00FF00");
                GM_setValue("tag_bcolor_not_exist", bcolor_list[1] || "#FF0000");
                GM_setValue("tag_bcolor_need_login", bcolor_list[2] || "#0000FF");
                GM_setValue("tag_bcolor_error", bcolor_list[3] || "#FFFF00");
            } catch (e) {
                alert("解析输入出错");
            }
        }
    }
    GM_registerMenuCommand("更改标签背景色", changeTagBColor);

    function changeTagFColor() {
        let now_fcolor_list = [GM_getValue("tag_fcolor_exist", "#000000"), GM_getValue("tag_fcolor_not_exist", "#000000"), GM_getValue("tag_fcolor_need_login", "#000000"), GM_getValue("tag_fcolor_error", "#000000")];
        let name = prompt("请依次输入代表'资源存在','资源不存在','站点需要登陆','站点解析错误'颜色的Hex值，并用英文逗号分割。当前值为：", `${now_fcolor_list.join(',')}`);
        if (name != null && name !== "") {
            try {
                let fcolor_list = name.split(",");
                GM_setValue("tag_fcolor_exist", fcolor_list[0] || "#000000");
                GM_setValue("tag_fcolor_not_exist", fcolor_list[1] || "#000000");
                GM_setValue("tag_fcolor_need_login", fcolor_list[2] || "#000000");
                GM_setValue("tag_fcolor_error", fcolor_list[3] || "#000000");
            } catch (e) {
                alert("解析输入出错");
            }
        }
    }
    GM_registerMenuCommand("更改标签文字色", changeTagFColor);

    function forceCacheClear() {
        if (confirm("清空所有缓存信息（包括资源存在情况、登陆情况等）")) {
            clearExpiredCacheValue(true);
        }
    }
    GM_registerMenuCommand("清空脚本缓存", forceCacheClear);
}


let fetch_anchor = function (anchor) {
    return anchor[0].nextSibling.nodeValue.trim();
};

function starBlock(source, source_link, _rating, _vote, max = 10) {
    let starValue = parseFloat(_rating) / 2;
    starValue = starValue % 1 > 0.5 ? Math.floor(starValue) + 0.5 : Math.floor(starValue);
    starValue *= (100 / max);

    return `<div class=rating_logo >${source} 评分</div><div class="rating_self clearfix" typeof="v:Rating"><strong class="ll rating_num" property="v:average">${parseFloat(_rating).toFixed(1)}</strong><span property="v:best" content=10.0 ></span><div class="rating_right "><div class="ll bigstar ${'bigstar' + starValue}"></div><div class="rating_sum"> <a href=${source_link}  class=rating_people target="_blank"><span property="v:votes">${_vote}</span>人${source === "MAL" ? "观看" : "评价"}</a> </div> </div> </div>`
}

function parseLdJson (raw) {
    return JSON.parse(raw.replace(/\n/ig,''));
}
 //PLEX库查找开始---DIY
  function PlexFunc() {
      // 页面匹配
      function DocumentReady(imdb_id, unititle, douban_id, year, eng_title) {
        const embyHost = "http://localhost:8096";
        const embyApiKey = "47dd";
        const plexHost = "https://plex.xxxx.com:32400";
        const mrHost = "https://mr.xxxx.com:1329";
        const mrHostSSL = "https://mr.xxxx.com:1329";
        const mrToken = "6GgDVeq7xxxxxxB5dZ2nmY";
        const tmdb = "https://www.themoviedb.org";
          if (!embyHost || !embyApiKey || !mrHost || !mrToken || !tmdb || !plexHost || !mrHostSSL) return;
          // 优先插入其他文字
          // 订阅按钮添加ID方便监听
          $("#content h1").after(`<a id="subscribe-btn" style="display:inline-block; background-color: #1d8b37; color: white; margin:0px 5px 5px 0px;font-weight: bold; font-size: 13px; padding: 3px 20px; border-radius: 5px; text-align: center;">订阅</a> | <a href='${mrHost}/movie/search?keyword=${imdb_id}&cates=Movie,TV,Documentary,Anime&searchMediaServer=true&searchSite=true&searchDouban=true' target='_blank'>精准搜索</a> | <a href='${mrHost}/movie/search?keyword=${unititle}${year}&cates=Movie,TV,Documentary,Anime&searchMediaServer=true&searchSite=true&searchDouban=true' target='_blank'>年份搜索</a> | <a href='${mrHost}/movie/search?keyword=${unititle}&cates=Movie,TV,Documentary,Anime&searchMediaServer=true&searchSite=true&searchDouban=true' target='_blank'>模糊搜索</a> | <a href=https://springsunday.net/torrents.php?search=${imdb_id}&search_area=4&search_mode=0' target='_blank'>不可说</a> | <a href=https://pt.keepfrds.com/torrents.php?search=${imdb_id}&search_area=4&search_mode=0' target='_blank'>月月</a> | <a href=https://kp.m-team.cc/torrents.php?incldead=0&spstate=0&inclbookmarked=0&search=${unititle}&search_area=0&search_mode=0' target='_blank'>馒头</a> | <a href=https://chdbits.co/torrents.php?search=${imdb_id}&search_area=4&search_mode=0' target='_blank'>岛</a>
 | <a href='${tmdb}/search?query=${unititle}' target='_blank'>TMDB中文</a> | <a href='${tmdb}/search?query=${eng_title}' target='_blank'>TMDB英文</a> | <a href='https://so.zimuku.org/search?q=${unititle}' target='_blank'>字幕库</a> | <a href='${plexHost}/web/index.html#!/search?query=${unititle}' target='_blank'>PLEX搜索</a> | <a href='${mrHost}/api/media/search_by_keyword?access_key=${mrToken}&keyword=${unititle}' target='_blank'>库详情</a>`);
        // 监听请求按钮
        $("#subscribe-btn").click(function (event) {
            MRSubscribe(douban_id);
        });
        // 提交POST请求订阅
        const MRSubscribe = (douban_id) => {
            let subscrib_url = `${mrHostSSL}/api/subscribe/sub_douban?access_key=${mrToken}`;
            let xhr = new XMLHttpRequest();
            xhr.open("POST", subscrib_url, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.timeout = 45e3;
            xhr.onload = function () {
                alert(JSON.parse(xhr.responseText).message);
            };
            const requestBody = JSON.stringify({
                "id": parseInt(douban_id)
            });
            xhr.send(requestBody);
          };
        // 根据关键词查询
          const checkMR = (keyword) => {
              let checkUrl = `${mrHost}/api/media/search_by_keyword?keyword=${keyword}&access_key=${mrToken}`
              GM_xmlhttpRequest({
                  method: "GET",
                  url: checkUrl,
                  timeout: 45e3,
                  onload: function (resPlex) {
                      let resText = resPlex.responseText;
                      let parPlex = JSON.parse(resText);
                      const returnCode = parPlex.code;
                      if (returnCode != 0) {
                          alert('根据名称查询机器人接口错误：' + parPlex.message);
                      } else {
                          const isFuzzyQuery = !imdb_id;
                          if (parPlex.data.length> 0) {
                              const text = isFuzzyQuery ? "🎲 媒体疑似存在" : "✅ 媒体库中已存在";
                              const textys = isFuzzyQuery ? "#FFA228" : "#1d8b37";
                              $("#content").prepend(`<a href='${plexHost}/web/index.html#!/search?query=${unititle}' target='_blank' style="background-color: rgba(1,1,1,0); margin:0px 2px 0px 5px; color:${textys};font-weight:bold;font-size:14px">${text}</a>`);
                          } else {
                             // 订阅按钮添加ID方便监听
                            $("#content").prepend(`<a id="subscribe-btn" style="background-color: rgba(1,1,1,0); margin:0px 2px 5px 3px; color:#ff6c00;font-weight:bold;font-size:14px";cursor: pointer;>🔔 媒体库中不存在</a>`)
                            //监听请求按钮
                            $("#subscribe-btn").click(function (event) {
                                MRSubscribe(douban_id);
                            });
                          }
                      }
                  }
              })
          };
        checkMR(imdb_id || unititle)
      }
      return {
          DocumentReady
      }
  }
  //PLEX库查找END

$(document).ready(function () {
    let douban_link, douban_id;

    douban_link = 'https://' + location.href.match(/douban.com\/subject\/\d+\//); //豆瓣链接
    douban_id = location.href.match(/(\d{7,8})/g);

    let site_map = [];

    /** label对象键值说明：
     * name:          String  站点名称，请注意该站点名称在不同的site_map中也应该唯一，以免脚本后续判断出错
     * method：       String  搜索请求方式，默认值为 "GET"
     * link：         String  构造好的请求页面链接，作为label的href属性填入，用户应该能直接点开这个页面。
     * ajax：         String  如果站点使用ajax的形式加载页面，则需要传入该值作为实际请求的链接，即优先级比link更高。
     * type：         String  返回结果类型，脚本默认按html页面解析；只有当传入值为"json"时，脚本按JSON格式解析
     * selector：     String  搜索成功判断结果，默认值为 "table.torrents:last > tbody > tr:gt(0)" (适用于国内多数NexusPHP构架的站点)
     *                        如果type为"page"（默认）时，为一个（jQuery）CSS选择器，
     *                        如果type为"json"或"jsonp"时，为一个具体的判断式。
     * selector_need_login    搜索需要登录的选择器，仅在type为默认时有用，其余用法同Selector一致。
     * data：         String  作为请求的主体发送的内容，默认为空即可
     * headers：      Object  修改默认请求头，（防止某些站点有referrer等请求头检查
     * rewrite_href:  Boolean 如果站点最终搜索显示的页面与实际使用搜索页面（特别是使用post进行交互的站点）不一致，
     *                        设置为true能让脚本存储最终url，并改写label使用的href属性
     * csrf:          Object  一个类似这样的字典 { name: "_csrf", update: "link"}
     *                        其中key为站点csrf防护的名称，update为需要更新的字段（一般为link或data）
     *
     * 注意： 1. 如果某键有默认值，则传入值均会覆盖默认值
     *        2. 关于请求方法请参考：https://github.com/scriptish/scriptish/wiki/GM_xmlhttpRequest
     * */
    if (douban_id) {
        clearExpiredCacheValue(false); // 清理缓存
        let cache = CacheStorage(douban_id, 86400 * 7 * 1e3);
        let need_login_cache = CacheStorage("need_login", 86400 * 1e3);

        $("#content div.aside").prepend(`<div id="drdm_req_status" style="color: #C65E24;background: #F4F4EC; border-radius: 8px; padding: 10px; margin-bottom: 20px; word-wrap: break-word;display: none;">
<div style="text-align: center;">豆瓣资源下载大师 - 资源搜索情况 <a href="javascript:void();" id="drdm_req_status_hide">(隐藏)</a> <hr></div>
<p id="drdm_dep_notice" style="color: #C65E24;display:none;">脚本未完全加载，部分站点将受影响。请确保网络稳定或尝试重新刷新页面。</p>
<table>
<tr><td width="50%">存在：<span id="drdm_req_success"></span></td><td width="50%">不存在：<span id="drdm_req_noexist"></span></td></tr>
<tr><td width="50%">请求中：<span id="drdm_req_asking"></span></td><td width="50%">失败或需要登陆：<span id="drdm_req_fail"></span></td></tr>
</table>
<span id="drdm_req_help"><hr>
<span>是否隐藏当前未成功的搜索项？  <a href="javascript:void();" id="drdm_hide_fail"> 是 </a>  /  <a href="javascript:void();" id="drdm_show_all"> 否 </a></span>
</span>
</div>
<div id='drdm_sites'></div>`);
        $("#drdm_req_status_hide").click(function () { $("#drdm_req_status").hide();});
        $("#drdm_hide_fail").click(function () {
            $("#drdm_sites a[title!=\"资源存在\"]").hide();
            $('#drdm_sites > div.c-aside.name-offline').each(function () {let that = $(this); if (that.find('> div > ul > a:visible').length == 0) {that.hide()}});
        });
        $("#drdm_show_all").click(function () { $("#drdm_sites a:hidden").show(); $('#drdm_sites > div.c-aside.name-offline').show(); });

        let update_status_interval;

        function update_req_status() {
            let asking_length = $("#drdm_sites a[title=\"正在请求信息中\"]").length;

            $("#drdm_req_success").text($("#drdm_sites a[title=\"资源存在\"]").length);
            $("#drdm_req_asking").text(asking_length);
            $("#drdm_req_noexist").text($("#drdm_sites a[title=\"资源不存在\"]").length);
            $("#drdm_req_fail").text($("#drdm_sites a[title=\"站点需要登陆\"]").length + $("#drdm_sites a[title=\"遇到问题\"]").length);

            if (asking_length === 0) {
                clearInterval(update_status_interval); // 当所有请求完成后清除定时器
                if (GM_getValue('enalbe_adv_auto_tip_hide', false)) {
                    $("#drdm_req_status_hide").click();
                }
            }
        }

        function _encodeToGb2312(str, opt) {
            let ret = "";
            try {
                ret = encodeToGb2312(str, opt);
            } catch (e) {
                ret = Math.random() * 1e6;
                $("#drdm_dep_notice").show();
            }
            return ret;
        }

        if (location.host === "movie.douban.com") {
            // 查看原图
            if ($('#mainpic p.gact').length === 0) { // 在未登录的情况下添加空白元素以方便查看原图交互按钮的定位
                $("#mainpic").append("<p class=\"gact\"></p>");
            }
            let posterAnchor = document.querySelector('#mainpic > a > img');
            let postersUrl, rawUrl;
            if (posterAnchor) {
                postersUrl = posterAnchor.getAttribute("src");
                rawUrl = postersUrl.replace(/photo\/[sl](_ratio_poster|pic)\/public\/(p\d+).+$/, "photo/raw/public/$2.jpg");
                $('#mainpic p.gact').after(`<a target="_blank" rel="nofollow" href="${rawUrl}">查看原图</a>`);
            }

            // 调整底下剧情简介的位置
            let interest_sectl_selector = $('#interest_sectl');
            interest_sectl_selector.after($('div.grid-16-8 div.related-info'));
            interest_sectl_selector.attr('style', 'float:right');
            $('div.related-info').attr('style', 'width:480px;float:left');

            // Movieinfo信息生成相关
            let this_title, trans_title, aka;
            let year, region, genre, language, playdate;
            let imdb_link, imdb_id, imdb_average_rating, imdb_votes, imdb_rating;
            let douban_average_rating, douban_votes, douban_rating;
            let episodes, duration;
            let director, writer, cast;
            let tags, introduction, awards;

            // 获得 <script type="application/ld+json" /> 里面的信息，这里面的东西和API返回需要的东西差不多
            let ld_json;
            try {
                ld_json = parseLdJson($('head > script[type="application/ld+json"]').text());
            } catch (e) {}

            // 增加Mediainfo的交互按钮与监听
            if (GM_getValue("enable_mediainfo_gen", false)) {
                $("div#info").append("<br><span class=\"pl\">生成信息: </span><a id='movieinfogen' href='javascript:void(0);'>movieinfo</a>");
                $("div.related-info").before("<div class='c-aside' style='float:left;margin-top:20px;width: 470px;display: none' id='movieinfo_div'><h2><i>电影简介</i>· · · · · · </h2><a href='javascript:void(0);' id='copy_movieinfo'>点击复制</a><div class=\"c-aside-body\" style=\"padding: 0 12px;\" id='movieinfo'></div></div>");
                $("a#movieinfogen").click(function () {
                    let descr = "";
                    descr += poster ? `[img]${poster}[/img]\n\n` : "";
                    descr += trans_title ? `◎译　　名　${trans_title}\n` : "";
                    descr += this_title ? `◎片　　名　${this_title}\n` : "";
                    descr += year ? `◎年　　代　${year.trim()}\n` : "";
                    descr += region ? `◎产　　地　${region}\n` : "";
                    descr += genre ? `◎类　　别　${genre}\n` : "";
                    descr += language ? `◎语　　言　${language}\n` : "";
                    descr += playdate ? `◎上映日期　${playdate}\n` : "";
                    descr += imdb_rating ? `◎IMDb评分  ${imdb_rating}\n` : ""; // 注意如果长时间没能请求完成imdb信息，则该条不显示
                    descr += imdb_link ? `◎IMDb链接  ${imdb_link}\n` : "";
                    descr += douban_rating ? `◎豆瓣评分　${douban_rating}\n` : "";
                    descr += douban_link ? `◎豆瓣链接　${douban_link}\n` : "";
                    descr += episodes ? `◎集　　数　${episodes}\n` : "";
                    descr += duration ? `◎片　　长　${duration}\n` : "";
                    descr += director ? `◎导　　演　${director}\n` : "";
                    descr += writer ? `◎编　　剧　${writer}\n` : "";
                    descr += cast ? `◎主　　演　${cast.replace(/\n/g, '\n' + '　'.repeat(4) + '  　').trim()}\n` : "";
                    descr += tags ? `\n◎标　　签　${tags}\n` : "";
                    descr += introduction ? `\n◎简　　介\n\n　　${introduction.replace(/\n/g, '\n' + '　'.repeat(2))}\n` : "";
                    descr += awards ? `\n◎获奖情况\n\n　　${awards.replace(/\n/g, '\n' + '　'.repeat(2))}\n` : "";
                    $("div#movieinfo").html(descr.replace(/\n/ig, "<br>"));
                    $("#movieinfo_div").toggle();
                });
                $("a#copy_movieinfo").click(function () {
                    let movieclip = $("#movieinfo").html().replace(/<br>/ig, "\n").replace(/<a [^>]*>/g, "").replace(/<\/a>/g, "");
                    GM_setClipboard(movieclip);
                    $(this).text("复制成功");
                });
            }

            // 先对一些关键信息进行判断
            let aka_anchor = $('#info span.pl:contains("又名")');
            let has_aka = aka_anchor.length > 0;
            let is_movie = $("a.bn-sharing[data-type='电影']").length > 0;
            let is_series = $("a.bn-sharing[data-type='电视剧']").length > 0;
            let is_anime = $('span[property="v:genre"]:contains("动画")').length > 0;
            let is_document = $('span[property="v:genre"]:contains("纪录片")').length > 0;

            // 页面元素定位
            let regions_anchor = $('#info span.pl:contains("制片国家/地区")'); //产地
            let language_anchor = $('#info span.pl:contains("语言")'); //语言
            let episodes_anchor = $('#info span.pl:contains("集数")'); //集数
            let duration_anchor = $('#info span.pl:contains("单集片长")'); //片长

            let imdb_anchor = $('#info span.pl:contains("IMDb")'); // IMDb
            let has_imdb = imdb_anchor.length > 0;

            // 基础Movieinfo信息
            let chinese_title = document.title.replace('(豆瓣)', '').trim();
            let foreign_title = $('#content h1>span[property="v:itemreviewed"]').text().replace(chinese_title, '').trim();
            let poster = rawUrl ? rawUrl.replace('raw','l_ratio_poster').replace('img3','img1') : '';

            if (has_aka) {
                aka = fetch_anchor(aka_anchor).split(' / ').sort(function (a, b) { //首字(母)排序
                    return a.localeCompare(b);
                }).join('/');
            }

            if (foreign_title) {
                trans_title = chinese_title + (aka ? ('/' + aka) : '');
                this_title = foreign_title;
            } else {
                trans_title = aka ? aka : '';
                this_title = chinese_title;
            }

            playdate = $('#info span[property="v:initialReleaseDate"]').map(function () {  //上映日期
                return $(this).text().trim();
            }).toArray().sort(function (a, b) {//按上映日期升序排列
                return new Date(a) - new Date(b);
            }).join('/');

            year = ' ' + $('#content > h1 > span.year').text().substr(1, 4);
            region = regions_anchor[0] ? fetch_anchor(regions_anchor).split(' / ').join('/') : '';
            language = language_anchor[0] ? fetch_anchor(language_anchor).split(' / ').join('/') : '';
            episodes = episodes_anchor[0] ? fetch_anchor(episodes_anchor) : '';
            duration = duration_anchor[0] ? fetch_anchor(duration_anchor) : $('#info span[property="v:runtime"]').text().trim();

            let is_europe = region.match(/美国|英国|加拿大|丹麦/);
            let is_japan = region.match(/日本/);
            let is_korea = region.match(/韩国/);
            let is_thai = region.match(/泰国/);
            let is_india = region.match(/印度/);
            let is_pakistan = region.match(/巴基斯坦|Pakistan/)
            let is_mainland = region.match(/中国大陆/);
            let is_mandarine = language.match(/汉语普通话/);
            let is_otherlan = language.match(/\//);

            genre = $('#info span[property="v:genre"]').map(function () { //类别
                return $(this).text().trim();
            }).toArray().join('/');

            // 获取电影名
            let title = $('#content > h1 > span')[0].textContent.split(' ').shift().replace(/[，]/g, " ").replace(/：.*$/, "");
            let eng_title = [this_title, trans_title].join("/").split("/").filter(function (arr) {
                return /([a-zA-Z]){2,}/.test(arr);
            })[0] || "";
            let is_chinese = title.match(/[^\x00-\xff]/);
            let unititle = is_chinese ? title : eng_title;

            // 剧集修正季数名
            eng_title = eng_title.match(/Season\s\d\d/) ? eng_title.replace(/Season\s/, "S") : eng_title.replace(/Season\s/, "S0");
            eng_title = eng_title.replace(/[:,!\-]/g, "").replace(/ [^a-z0-9]+$/, "").replace(/ +/g," ");
            let eng_title_clean = eng_title.replace(/ S\d\d*$/, "");
            let has_entitle= eng_title_clean;

            // 日剧春夏秋冬解析
            let playdate_pro = new Date(playdate.split('/')[0]);
            let release_year = playdate.replace(/-.*$/, "").replace(/^\d{2}/, "");
            let release_month = playdate_pro.getMonth() + 1;
            let drama_season;
            if ([4, 5, 6].includes(release_month)) { drama_season = "spring"; }
            else if ([7, 8, 9].includes(release_month)) { drama_season = "summer"; }
            else if ([10, 11, 12].includes(release_month)) { drama_season = "autumn"; }
            else { drama_season = "winter"; }

            // 电影+年份 (只有电影才搜索并赋值年份)
            let encode_year = is_movie ? year.replace(/ /, "_") : "";
            let nian = is_movie ? year : "";
            let encode_this_title = (this_title || "").replace(/:/, "").replace(/ /g, "_");
            let ptzimu = encode_this_title + encode_year;
            chinese_title = chinese_title.replace(/[：，]/, " ");
            let gunititle = _encodeToGb2312(unititle, true);
            let punititle = encodeURI(unititle).replace(/%/g, "%25");
            let uunititle = encodeURI(unititle).replace(/%/g, "_");
            let ywm = eng_title + nian;
            let zwm = chinese_title + nian;
            let entitle = eng_title_clean + nian
            let is_ywm = ywm.match(/[A-Z]/);

            // Add top rank tag
            if (GM_getValue("enable_top_rang_tag", true)) {
                GM_xmlhttpRequest({
                    method: 'GET',
                    url: "https://bimzcy.github.io/rank4douban/data.json",
                    onload: function (response) {
                        let rank_json = JSON.parse(response.responseText);
                        let insert_html_list = [];
                        for (let i in rank_json) {
                            let top_list = rank_json[i];
                            let list_num = top_list.list[douban_id];
                            if (list_num) {
                                let list_order = top_list.top;
                                insert_html_list[list_order] = `<div class="top250"><span class="top250-no">${top_list.prefix ? top_list.prefix : "No."}${list_num}</span><span class="top250-link"><a href="${top_list.href}" title="${top_list.title}">${top_list.short_title}</a></span></div>`;
                            }
                        }
                        if (insert_html_list) {
                            insert_html_list.push("<div style=\"display: none;\" id='rank_toggle' data-toggle='show'><a href=\"javascript::\">展示剩余 →</a></div>");
                            let after = $("#dale_movie_subject_top_icon") || $("#content > h1");
                            after.before(insert_html_list.join(' '));
                            let top_selector = $(".top250");
                            top_selector.css("display", "inline-block");
                            if (top_selector.length > 4) {
                                $(".top250:gt(3)").hide();
                                $("#rank_toggle").show().css("display", "inline-block").click(function () {
                                    if ($(this).attr("data-toggle") === "show") {
                                        top_selector.show();
                                        $(this).attr("data-toggle", "hide").html("<a href=\"javascript::\">隐藏剩余 ←</a>");
                                    } else {
                                        $(".top250:gt(3)").hide();
                                        $(this).attr("data-toggle", "show").css("display", "inline-block").html("<a href=\"javascript::\">展示剩余 →</a>");
                                    }
                                })
                            }
                        }
                    }
                });
            }

            // 从中栏中先获取豆瓣评分信息（此时还没有imdb等第三方评价信息）
            let douban_vote_another = $('div[typeof="v:Rating"]:eq(0)');
            if (douban_vote_another.length > 0) {
                douban_average_rating = douban_vote_another.find('[property="v:average"]').length > 0 ? douban_vote_another.find('[property="v:average"]').text() : 0;
                douban_votes = douban_vote_another.find('[property="v:votes"]').length > 0 ? douban_vote_another.find('[property="v:votes"]').text() : 0;
                douban_rating = douban_average_rating + '/10 from ' + douban_votes + ' users';
            }

            // 中栏加强
            $("div#interest_sectl").append(`<div class='rating_wrap clearbox' id='loading_more_rate'>加载第三方评价信息中.......</div>
<div class="rating_wrap clearbox rating_imdb" style="display:none"></div>
<div class="rating_wrap clearbox rating_rott" style="display:none"></div>
<div class="rating_wrap clearbox rating_anidb" style="border-top: 1px solid #eaeaea; display:none"></div>
<div class="rating_more" style="display:none"></div>`); // 修复部分情况$("div.rating_betterthan")不存在情况

            // put on more ratings
            let rating_more_data = [ /** {name, link || `${imdb_link}`, text} */ ];

            function update_rating_more(data) {
                rating_more_data.push(data);

                let rating_more = $('#interest_sectl .rating_more');
                let rating_more_html = '';
                for (let i = 0; i < rating_more_data.length; i++) {
                    let rating_data = rating_more_data[i];
                    rating_more_html +=`<div>${rating_data['name']} <a href='${rating_data['link'] || imdb_link}' style="${ rating_data['name'].length <= 4 ? 'margin-left:-20px' : ''} " target="_blank" title="${rating_data['data']}">${rating_data['data']}</a></div>`;
                }
                rating_more.html(rating_more_html);
                rating_more.show();
                $("#loading_more_rate").hide();
            }

            // 请求IMDb信息（最慢，最先且单独请求）DIY
            if (has_imdb) {
                imdb_id = fetch_anchor(imdb_anchor);
                PlexFunc().DocumentReady(imdb_id, unititle, douban_id, year, eng_title);
                imdb_link = `https://www.imdb.com/title/${imdb_id}/`

                // 把豆瓣删除的超链接给加回去
                $(imdb_anchor[0].nextSibling).replaceWith(`&nbsp;<a href="${imdb_link}" target="_blank">${imdb_id}</a>`);

                getDoc(imdb_link, null, function (doc) {
                    // 判断是不是新版界面
                    let new_another = $('script#__NEXT_DATA__', doc);
                    let is_new = new_another.length > 0;
                    let ld_json_imdb;

                    try {
                        // IMDb 评分 （评分信息直接从 ld_json 中获取算了）
                        ld_json_imdb = parseLdJson($('head > script[type="application/ld+json"]', doc).text());
                        imdb_average_rating = ld_json_imdb["aggregateRating"]["ratingValue"];
                        imdb_votes = ld_json_imdb["aggregateRating"]["ratingCount"];
                        imdb_rating = imdb_votes ? imdb_average_rating + '/10 from ' + imdb_votes + ' users' : ''; // MovieinfoGen 相关
                        $('#interest_sectl div.rating_imdb').html(starBlock("IMDB", imdb_link + 'ratings?ref_=tt_ov_rt', imdb_average_rating, imdb_votes)).show();

                        // 分级信息 可以从 ld_json 中获取
                        if (ld_json_imdb['contentRating']) {
                            const contentRatingMap = {
                                'G': '大众级 | 全年龄',
                                'PG': '指导级 | ≥6岁',
                                'PG-13': '特指级 | ≥13岁',
                                'NC-17': '限定级 | ≥17岁',
                                'R': '限制级 | ≥18岁',
                                'Not Rated': '未分级'
                            };
                            update_rating_more({
                                name: '分级', // MPAA
                                link: imdb_link + 'parentalguide#certification',
                                data: contentRatingMap[ld_json_imdb['contentRating']] || ld_json_imdb['contentRating']
                            });
                        }

                        // Metascore
                        let metascore_selector = is_new ? 'a[href*="criticreviews"] span.score' : 'a[href^=criticreviews] span';
                        if ($(metascore_selector, doc).length > 0) {
                            update_rating_more({
                                name: 'Metascore',
                                link: imdb_link + 'criticreviews?ref_=tt_ov_rt',
                                data: $(metascore_selector, doc).text()
                            });
                        }

                        // 流行度
                        let popularity_selector = is_new
                        ? 'div[class^="TitleBlockButtonBase__ButtonContentWrap"]:has( > div[class^="TrendingButton__ContentWrap"])'
                        : 'div:contains("Popularity") + div > span.subText';
                        if ($(popularity_selector, doc).length > 0) {
                            let popularity_another = $(popularity_selector, doc);
                            let pop_score, pop_delta, pop_up;
                            if (is_new) {
                                pop_score = popularity_another.find('div[class^="TrendingButton__TrendingScore"]').text();
                                pop_delta = popularity_another.find('div[class^="TrendingButton__TrendingDelta"]').text();
                                pop_up = popularity_another.find('svg.ipc-icon--arrow-drop-up').length > 0;
                            } else {
                                let pop_text_match = popularity_another.text().match(/(\d+)\n.+?(\d+)/i);
                                if (pop_text_match && pop_text_match.length >= 3) {
                                    pop_score = pop_text_match[1];
                                    pop_delta = pop_text_match[2];
                                    pop_up = popularity_another.find('span.popularityImageUp').length > 0;
                                }
                            }

                            if (pop_score) {
                                update_rating_more({
                                    name: '流行度',
                                    link: imdb_link + 'criticreviews?ref_=tt_ov_rt',
                                    data: `${pop_score} (${pop_up ? '∧' : '∨'}${pop_delta})`
                                });
                            }
                        }

                        // TODO let reviews;

                        // 从网页中获取的部分信息，要区分是否新版页面
                        if (GM_getValue("enable_imdb_ext_info", true)) {
                            if (is_new) {
                                if ($("li.ipc-metadata-list__item.fJEELB:contains('Budget')", doc).length > 0) {
                                    update_rating_more({
                                        name: '总成本',
                                        data: $("li.ipc-metadata-list__item.fJEELB:contains('Budget')", doc).text().replace(/^Budget/, '').replace(/\(estimated\)/,'')
                                    });
                                }
                                if ($("li.ipc-metadata-list__item.fJEELB:contains('Opening weekend US & Canada')", doc).length > 0) {
                                    update_rating_more({
                                        name: '美首周',
                                        data: $("li.ipc-metadata-list__item.fJEELB:contains('Opening weekend US & Canada')", doc).text().replace(/^Opening weekend US & Canada/, '').replace(/[a-zA-Z]+ \d+, \d+$/, '')
                                    });
                                }
                                if ($("li.ipc-metadata-list__item.fJEELB:contains('Gross US & Canada')", doc).length > 0) {
                                    update_rating_more({
                                        name: '美票房',
                                        data: $("li.ipc-metadata-list__item.fJEELB:contains('Gross US & Canada')", doc).text().replace(/^Gross US & Canada/, '')
                                    });
                                }
                                if ($("li.ipc-metadata-list__item.fJEELB:contains('Gross worldwide')", doc).length > 0) {
                                    update_rating_more({
                                        name: '总票房',
                                        data: $("li.ipc-metadata-list__item.fJEELB:contains('Gross worldwide')", doc).text().replace(/^Gross worldwide/, '')
                                    });
                                }
                                if ($("li.ipc-metadata-list__item:contains('Aspect ratio')", doc).length > 0) {
                                    update_rating_more({
                                        name: '宽高比',
                                        data: $("li.ipc-metadata-list__item:contains('Aspect ratio')", doc).text().replace(/^Aspect ratio/, '')
                                    });
                                }
                            } else { // 旧版代码
                                if ($("div.txt-block:contains('Budget:')", doc).length > 0) {
                                    update_rating_more({
                                        name: '总成本',
                                        data: $("div.txt-block:contains('Budget:')", doc).text().trim().replace(/\n/g, '').replace(/ .*$/, '').replace(/^Budget:/, '').replace(/CNY./, '¥').replace(/KRW./, '₩').replace(/JPY./, '円').replace(/HKD./, '港')
                                    });
                                }
                                if ($("div.txt-block:contains('Opening Weekend:'):not(:contains('USA:'))", doc).text().length > 0) {
                                    update_rating_more({
                                        name: '本首周',
                                        data: $("div.txt-block:contains('Opening Weekend:'):not(:contains('USA:'))", doc).text().trim().replace(/\n/g, '').replace(/^Opening Weekend:/, '').replace(/ \(.*$/, '').replace(/CNY./, '¥').replace(/KRW./, '₩').replace(/JPY./, '円').replace(/HKD./, '港')
                                    });
                                }
                                if ($("div.txt-block:contains('Opening Weekend USA:')", doc).text().length > 0) {
                                    update_rating_more({
                                        name: '美首周',
                                        data: $("div.txt-block:contains('Opening Weekend USA:')", doc).text().trim().replace(/\n/g, '').replace(/^Opening Weekend USA:/, '').replace(/,\d+ .*$/, '')
                                    });
                                }
                                if ($("div.txt-block:contains('Gross USA:')", doc).text().length > 0) {
                                    update_rating_more({
                                        name: '美票房',
                                        data: $("div.txt-block:contains('Gross USA:')", doc).text().trim().replace(/\n/g, '').replace(/^Gross USA:/, '').replace(/\, \d+ .*$/, '')
                                    });
                                }
                                if ($("div.txt-block:contains('Cumulative Worldwide Gross:')", doc).text().length > 0) {
                                    update_rating_more({
                                        name: '总票房',
                                        data: $("div.txt-block:contains('Cumulative Worldwide Gross:')", doc).text().trim().replace(/\n/g, '').replace(/^Cumulative Worldwide Gross:/, '').replace(/\, \d+ .*$/, '')
                                    });
                                }
                                if ($("div.txt-block:contains('Aspect Ratio:')", doc).text().length > 0) {
                                    update_rating_more({
                                        name: '宽高比',
                                        link: imdb_link + 'technical?ref_=tt_dt_spec',
                                        data: $("div.txt-block:contains('Aspect Ratio:')", doc).text().trim().replace(/\n/g, '').replace(/^Aspect Ratio:/, '')
                                    });
                                }
                            }
                        }
                    } catch (e) {
                        // throw e;
                    };

                    if (GM_getValue("enable_tomato_rate", true)) { //烂番茄评分显示功能
                        // add rottentomatoes block
                        let movieTitle = ld_json_imdb['name'].trim();
                        let rottURL = 'https://www.rottentomatoes.com/m/' + movieTitle.replace(/:|-/, "").replace(/\s+/g, "_").replace(/\W+/g, "").replace(/_+/g, "_").toLowerCase();
                        getDoc(rottURL, null, function (rotdoc) {
                            $('#interest_sectl div.rating_rott').html(`<span class="rating_logo ll">烂番茄评分</span><br><div id="rottValue" class="rating_self clearfix"></div></div>`).show();
                            if ($('script#score-details-json', rotdoc).length > 0) {
                                let rottJson = JSON.parse($('#score-details-json', rotdoc).text());
                                if (rottJson.modal && rottJson.modal.tomatometerScoreAll) {
                                    let tomatometerScoreAll = rottJson.modal.tomatometerScoreAll || {};
                                    let rating_rott_value = tomatometerScoreAll.score || 0;
                                    let fresh_rott_value = tomatometerScoreAll.likedCount || 0;
                                    let rotten_rott_value = tomatometerScoreAll.notLikedCount || 0;
                                    $('#interest_sectl .rating_rott #rottValue').append(`<strong class="ll rating_num"><a target="_blank" href="${rottURL}">${rating_rott_value}%</a></strong><div class="rating_right" style="line-height: 16px;"><span>鲜:&nbsp;&nbsp;${fresh_rott_value}</span><br><span>烂:&nbsp;&nbsp;${rotten_rott_value}</span></div>`);
                                }
                            }
                            else {
                                $('#interest_sectl div.rating_rott').append(`<br>搜索rotta: <a target='_blank' href='${'https://www.rottentomatoes.com/search/?search=' + encodeURI(movieTitle)}'>${movieTitle}</a>`);
                            }
                        });
                    }
                    $("#loading_more_rate").hide();
                });
            } else {
              //DIY
              PlexFunc().DocumentReady(imdb_id, unititle, douban_id, eng_title);
            }
            if (GM_getValue("enable_blue_date", true)) { //蓝光发售日期显示功能
                let ywm = eng_title.replace(/[:,!\-]/g, "").replace(/ /g,'-');
                let blueURL = 'https://www.releases.com/p/' + ywm.toLowerCase() + '/blu-ray/';
                getDoc(blueURL, null, function (bluedoc) {
                    let result_0 = $('span[title*="Blu-ray"][title*="release date"]:not(:contains("TBA")):first', bluedoc);
                    if (result_0.length > 0) {
                        let blueDate = new Date(result_0.text());
                        update_rating_more({  // 这种写法可能会导致 蓝光发售日期显示顺序飘忽不定，不过没有太大关系
                            name: '蓝光发售',
                            link: blueURL,
                            data: `${blueDate.getFullYear()}年${blueDate.getMonth()+1}月${blueDate.getDate()}日`
                        });
                    }
                });
            }

            if (GM_getValue("enable_anime_rate", true)) { //开启动漫评分显示功能
                // 如果是动漫，请求anydb的anidb、bgm、mal信息
                if (is_anime) {
                    getJSON("https://anydb.depar.cc/anime/query?_cf_cache=1&douban=" + douban_id, function (data1) {
                        let _anydb_html = "";
                        if (data1.success) {
                            let source_list = ["AniDB", "Bgm", "MAL"];
                            for (let i = 0; i < source_list.length; i++) {
                                let source = source_list[i];
                                let _data = data1.matched[source.toLowerCase()];
                                if (_data) {
                                    let _group = _data.rate.match(/([\d.]+?) \((\d+)\)/);
                                    let _rating = _group[1];
                                    let _vote = _group[2];
                                    _anydb_html += starBlock(source, _data.url, _rating, _vote);
                                }
                            }
                            if (_anydb_html.trim().length > 0) {
                                $('#interest_sectl > div.rating_anidb').html(_anydb_html).show();
                            }
                        }
                        $("#loading_more_rate").hide();
                    });
                }
            }

            if (GM_getValue("enable_mediainfo_gen", false)) { // 请求豆瓣附属信息用于Mediainfo生成
                GM_xmlhttpRequest({
                    method: 'GET',
                    url: douban_link + 'awards/',
                    headers: {
                        'Host' : 'movie.douban.com',
                        // 'Referer' : location.href,
                    },
                    onload: function (responseDetail) {
                        if (responseDetail.status === 200) {
                            let doc = page_parser(responseDetail.responseText);
                            awards = $('#content>div>div.article', doc).html()
                                .replace(/[ \n]/g, '')
                                .replace(/<\/li><li>/g, '</li> <li>')
                                .replace(/<\/a><span/g, '</a> <span')
                                .replace(/<(div|ul)[^>]*>/g, '\n')
                                .replace(/<[^>]+>/g, '')
                                .replace(/&nbsp;/g, ' ')
                                .replace(/ +\n/g, '\n')
                                .trim();
                        }
                    }
                }); // 该影片的评奖信息

                // 简介 （首先检查是不是有隐藏的，如果有，则直接使用隐藏span的内容作为简介，不然则用 span[property="v:summary"] 的内容）
                introduction = $('#link-report > span.all.hidden').length > 0 ? $('#link-report > span.all.hidden').text() : // 隐藏部分
                ($('[property="v:summary"]').length > 0 ? $('[property="v:summary"]').text() : '暂无相关剧情介绍');
                introduction = introduction.split('\n').map(function(a) {return a.trim()}).join('\n'); // 处理简介缩进
                // 导演，编剧，演员 （只能获取到显示的，没API丰富）
                let director_another = $('span > span:contains("导演")').parent('span'); // 往上回溯一级
                let writer_another = $('span > span:contains("编剧")').parent('span');
                let cast_another = $('span.actor');
                if (ld_json) {  // 优先使用ld_json中内容，没有则做页面解析
                    if (ld_json['director']) director = ld_json['director'].map(function (d) {return d['name']}).join(' / ');
                    if (ld_json['author']) writer = ld_json['author'].map(function (d) {return d['name']}).join(' / ');
                    if (ld_json['actor']) cast = ld_json['actor'].map(function (d) {return d['name']}).join('\n');
                }
                if (typeof director == 'undefined' && director_another.length > 0) director = director_another.find('a[href^="/celebrity"]').map(function() {return $(this).text()}).get().join(' / ');
                if (typeof writer == 'undefined' && writer_another.length > 0) writer = writer_another.find('a[href^="/celebrity"]').map(function() {return $(this).text()}).get().join(' / ');
                if (typeof cast == 'undefined' && cast_another.length > 0) cast = cast_another.find('a[href^="/celebrity"]').map(function() {return $(this).text()}).get().join('\n');

                // 标签
                let tag_another = $('div.tags-body > a[href^="/tag"]');
                if (tag_another.length > 0) tags = tag_another.map(function () {return $(this).text()}).get().join(' | ');
            }

            // 资源名称
            let zwzy = (unititle.replace(/ /g, ".").replace("：", ".").replace(/\.\./g, ".") + "." + eng_title.replace(": ", ".").replace(/ /g, ".") + "." + year.replace(/ /, "")).replace(/\.{2,}/g, ".");
            let imdbzy = has_imdb ? "." + imdb_id : "";
            $("div#info").append(`<br><span class=\"pl\">资源名称: </span>${zwzy}${imdbzy}`);

            let neizhan = has_imdb ? imdb_id : ('/subject/' + douban_id); // PT内站 智能判定是用IMDB ID还是豆瓣ID
            let gongwang = has_imdb ? imdb_id : douban_id;
            let jingzhun = has_imdb ? imdb_id : ywm;
            let dbzw = has_imdb ? imdb_id : unititle + nian;
            let unit3d = has_imdb ? "imdb=" + imdb_id.slice(2) : "search=" + ywm;
            let movieright = is_movie ? "movies" : "tv-shows";
            let avistaz = has_imdb ? "imdb=" + imdb_id : "search=" + ywm;

            if (_version === "完整版") {
                let npid = has_imdb ? ('imdb=' + imdb_id) : ('douban=' + douban_id); // NPUBITS 智能判定是用IMDB ID还是豆瓣ID
                let ttgid = has_imdb ? ('IMDB' + imdb_id.slice(2)) : zwm; // TTG 智能判定是用IMDB ID还是中文名
                let ptfriend = has_imdb ? (imdb_id + '&search_area=4') : (douban_id + '&search_area=5'); // PT之友 智能判定是用IMDB ID还是豆瓣ID
                let zxid = has_imdb ? imdb_id : zwm; // ZX 智能判定是用IMDB ID还是中文名
                let monid = has_imdb ? ('imdbId=' + imdb_id) : ( 'name=' + zwm); // MONIKA智能判定是IMDB ID还是中文名
                let spid = has_imdb ? (imdb_id + '&search_area=4') : (unititle + '&search_area=0'); // Spring、天空、馒头 智能判定是用IMDB ID还是中文名
                let leid = has_imdb ? (imdb_id + '&search_area=imdb') : (douban_id + '&search_area=douban'); // Lemon 智能判定是用IMDB ID还是豆瓣ID
                site_map.push({
                    name: "20万+种PT内站",
                    label: [
                        { name: "HDSky", link: 'https://hdsky.me/torrents.php?incldead=1&notnewword=1&search=' + spid, },
                        { name: "LemonHD", link: 'https://lemonhd.org/torrents.php?incldead=1&search_area=0&notnewword=1&search=' + leid, },
                        { name: "MTeam", link: 'https://kp.m-team.cc/torrents.php?incldead=1&notnewword=1&search=' + spid, },
                        { name: "PT之友", link: 'https://pterclub.com/torrents.php?incldead=1&notnewword=1&search=' + ptfriend, selector: "table.torrents table.torrentname" },
                        { name: "TTG", link: 'https://totheglory.im/browse.php?c=M&notnewword=1&search_field=' + ttgid, selector: "table#torrent_table:last > tbody > tr:gt(0)" },
                    ]
                });
                site_map.push({
                    name: "10万+种PT内站",
                    label: [
                        { name: "CCFBits", link: 'http://www.ccfbits.org/browse.php?fullsearch=1&notnewword=1&search=' + neizhan, selector: 'td[style="border:none;text-align:left"] a[title]', selector_need_login: "#loginform" },
                        { name: "CHDBits", link: 'https://chdbits.co/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "HDChina", link: 'https://hdchina.org/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, selector: "table.torrent_list:last > tbody > tr:gt(0)" },
                        { name: "OurBits", link: 'https://ourbits.club/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "SJTU", link: 'https://pt.sjtu.edu.cn/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, selector: "table.torrents:last > tbody > tr" },
                        { name: "TJUPT", link: 'https://www.tjupt.org/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, selector: "table.torrents table.torrentname" },
                    ]
                });
                site_map.push({
                    name: "5万+种PT内站",
                    label: [
                        { name: "Audience", link: 'https://audiences.me/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "BTSchool", link: 'http://pt.btschool.club/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan,/* selector: "table.torrents:last > tbody > tr:gt(0)"}, */ },
                        { name: "HDArea", link: 'https://www.hdarea.co/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, selector: "table.torrents table.torrentname", selector_need_login: "h1 span:contains('Checking your browser before accessing')" },
                        { name: "HDHome", link: 'https://hdhome.org/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "PTHOME", link: 'https://www.pthome.net/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "Spring", link: 'https://springsunday.net/torrents.php?incldead=1&notnewword=1&search=' + spid, },
                        { name: "聆音Club", link: 'https://pt.soulvoice.club/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                    ]
                });
                site_map.push({
                    name: "2万+种PT内站",
                    label: [
                        { name: "GHTT", link: 'https://www.hitpt.com/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, selector: "table.torrents table.torrentname" },
                        { name: "GPW", link: 'https://greatposterwall.com/torrents.php?searchstr=' + unititle, selector: ".TableTorrent-movieInfoBody .TableTorrent-movieInfoTitle" },
                        { name: "HDDolby", link: 'https://www.hddolby.com/torrents.php?incldead=1&search_area=1¬newword=1&search=' + neizhan, },
                        { name: "HD4FANS", link: 'https://pt.hd4fans.org/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "HDAtmos", link: 'https://hdatmos.club/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "HDFans", link: 'https://hdfans.org/torrents.php?incldead=1&search_area=1&newword=1&search=' + neizhan, },
                        { name: "HDTime", link: 'https://hdtime.org/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "HDU", link: 'http://pt.upxin.net/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "NYPT", link: 'https://nanyangpt.com/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, selector: "table.torrents:last > tbody > tr" },
                        { name: "PT时间", link: 'https://www.pttime.org/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "TCCF", link: 'https://et8.org/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "TLFBits", link: 'http://pt.eastgame.org/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "海胆之家", link: 'https://www.haidan.video/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, selector: "div.name_col.table_cell" },
                        { name: "烧包乐园", link: 'https://ptsbao.club/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                    ]
                });
                site_map.push({
                    name: "1万+种PT内站",
                    label: [
                        { name: "CarPT", link: 'https://carpt.net/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "DiscFan", link: 'http://discfan.net/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "FRDS", link: 'https://pt.keepfrds.com/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, selector: "table.torrents table.torrentname" },
                        { name: "JoyHD", link: 'https://www.joyhd.net/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, selector: "tr table.torrentname"},
                        { name: "Hares", link: 'https://club.hares.top/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, selector: "div.layui-torrents-title" },
                        { name: "HDCity", link: 'https://hdcity.city/pt?incldead=1&search_area=1&notnewword=1&iwannaseethis=' + neizhan, selector: "center > div > div > div.text" },
                        { name: "HHCLUB", link: 'https://hhanclub.top/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "HDZone", link: 'http://hdzone.me/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "PTMSG", link: 'https://pt.msg.vg/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "明教", link: 'https://hdpt.xyz/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "小蚂蚁", link: 'http://hdmayi.com/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                    ]
                });
                site_map.push({
                    name: "5千+种PT内站",
                    label: [
                        { name: "52PT", link: 'https://52pt.site/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan,/* selector: "table.torrents:last > tbody > tr:gt(0)"}, */ },
                        // { name: "HDAI", method: "post", link: 'http://www.hd.ai/Torrents.index?keyword=' + unititle, ajax:'http://www.hd.ai/Torrents.tableList', data:`{"keyword":"${unititle}"}`, headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8" }, selector: 'data.length > 0' },
                        { name: "BeiTai", link: 'http://www.beitai.pt/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan,/* selector: "table.torrents:last > tbody > tr:gt(0)"}, */ },
                        { name: "FreeFarm", link: 'https://pt.0ff.cc/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "HDVIDEO", link: 'https://hdvideo.one/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "OshenPT", link: 'http://www.oshen.win/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "丐帮", link: 'https://gainbound.net/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "龙之家", link: 'https://www.dragonhd.xyz/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "壹PT吧", link: 'https://1ptba.com/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                    ]
                });
                site_map.push({
                    name: "1千+种内站",
                    label: [
                        { name: "3Wmg", link: 'https://www.3wmg.com/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "ICC", link: 'https://www.icc2022.com/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "iHDBits", link: 'http://ihdbits.me/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "PT分享站", link: 'https://pt.itzmx.com/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "ZmPT", link: 'https://zmpt.cc/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "铂金学院", link: 'https://ptchina.org/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "海棠PT", link: 'https://www.htpt.cc/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "红叶", link: 'http://leaves.red/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "网络咖啡厅", link: 'http://www.ptnic.net/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                    ]
                });
                if (is_anime) {
                    site_map.push({
                        name: "PT动漫游戏",
                        label: [
                            { name: "AB", link: 'https://animebytes.tv/torrents.php?searchstr=' + ywm, selector: "div.thin > div.group_cont" },
                            { name: "AT", link: 'https://animetorrents.me/torrents.php?search=' + eng_title, ajax: 'https://animetorrents.me/ajax/torrents_data.php?total=1&search=' + eng_title + '&SearchSubmit=&page=1', headers: { "x-requested-with": "XMLHttpRequest" }, rewrite_href: false, selector: 'table.dataTable > tbody > tr:nth-child(2)', selector_need_login: "h1.headline strong:contains('Access Denied!')" },
                            { name: "BakaBT", link: 'https://bakabt.me/browse.php?q=' + ywm, selector: "table.torrents > tbody > tr:gt(0)", selector_need_login: "#loginForm" },
                            { name: "CC", link: 'http://www.cartoonchaos.org/index.php?page=torrents&options=0&active=1&search=' + ywm, selector: "table > tbody > tr:nth-child(2) > td > table > tbody > tr:nth-child(2) > td > table > tbody > tr:gt(0)", selector_need_login: "table[style='border-color:#E70000']" },
                            { name: "MONIKA", link: 'https://monikadesign.uk/torrents?' + monid, selector: "td.torrent-listings-overview" },
                            { name: "SkySnow", link: 'https://skyeysnow.com/forum.php?mod=torrents&notnewword=1&search=' + unititle + nian, selector: "table.torrents > tbody > tr:gt(0)" },
                            { name: "U2", link: 'https://u2.dmhy.org/torrents.php?incldead=1&search_area=0&notnewword=1&search=' + this_title, },
                        ]
                    });
                }
                site_map.push({
                    name: "PT影视IPV6",
                    label: [
                        { name: "6V", method: "POST", link: 'http://bt.neu6.edu.cn/search.php?mod=forum', selector: '#threadlist > table > tbody > tr:gt(0)', data: `srchtxt=${gunititle}&srchfilter=all&srchfrom=0&before=0&orderby=lastpost&ascdesc=desc&srchfid[]=all&searchsubmit=yes`,headers: {"Content-Type": "application/x-www-form-urlencoded"},rewrite_href:true,csrf: {name: "formhash", update:"data"}},
                        { name: "BYRBT", link: 'https://bt.byr.cn/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "HUDBT", link: 'https://hudbt.hust.edu.cn/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "NPUBITS", link: 'https://npupt.com/torrents.php?incldead=1&search_area=1&notnewword=1&' + npid, selector: "#torrents_table > tbody > tr:gt(0)" },
                        { name: "NWSUAF", link: 'https://pt.nwsuaf6.edu.cn/torrents.php?incldead=1&search_area=1&notnewword=1&search=' + neizhan, },
                        { name: "PT江湖", method: "POST", link: 'http://www.dutpt.com/search.php?mod=forum', selector: '#threadlist li.pbw', data: `srchtxt=${unititle}&searchsubmit=yes`,headers: {"Content-Type": "application/x-www-form-urlencoded"},rewrite_href:true,csrf: {name: "formhash", update:"data"}, selector_need_login: "#messagetext" },
                        { name: "ZX", link: 'http://pt.zhixing.bjtu.edu.cn/search/x' + zxid + '-notnewword=1/', selector: "table.torrenttable > tbody > tr:gt(1)" },
                    ]
                });
                if (has_imdb) {
                    site_map.push({
                        name: "NZB终身影视",
                        label: [
                            { name: "altHUB", link: 'https://althub.co.za/search/' + ywm, selector: "#browsetable a.title", selector_need_login: "#modalLogin" },
                            { name: "Crawler", link: 'https://www.usenet-crawler.com/advsearch?searchadvr=' + ywm, selector: "#browsetable a.title", selector_need_login: "#modalLogin" },
                            { name: "Miatrix", link: 'https://www.miatrix.com/search/' + ywm, selector: "#browsetable > tbody > tr:gt(0)", selector_need_login: "form[action='login']" },
                            { name: "Ninja", link: 'http://ninjacentral.co.za/search/' + ywm, selector: "#browsetable a.title", selector_need_login: "form[action='login']" },
                            { name: "NZBCat", link: 'https://nzb.cat/search/' + ywm, selector: "#browsetable > tbody > tr:gt(0)", selector_need_login: "form[action='login']" },
                            { name: "NZBgeek", link: 'https://nzbgeek.info/geekseek.php?movieid=' + imdb_id.slice(2), selector: "table > tbody > tr.HighlightTVRow2:gt(0)", selector_need_login: "input[value='do_login']" },
                            { name: "NZBGrab", link: 'https://www.nzbgrabit.xyz/nzbsearch.php?query=' + imdb_id, selector: "h3.threadtitle", selector_need_login: "form[action='login.php?do=login']" },
                            { name: "NZBP", link: 'https://nzbplanet.net/search/' + ywm, selector: "#browsetable > tbody > tr:gt(0)", selector_need_login: "form[action='login']" },
                            { name: "NZBs2GO", link: 'https://nzbs2go.com/search?id=' + ywm, selector: "#browsetable > tbody > tr:gt(0)", selector_need_login: "form[action='login']" },
                            { name: "Oznzb", link: 'https://www.oznzb.com/search/' + ywm, selector: "#browsetable > tbody > tr.ratingReportContainer:gt(0)", selector_need_login: "#login" },
                            { name: "SNZB", link: 'https://simplynzbs.com/search/' + ywm, selector: "#browsetable > tbody > tr:gt(0)", selector_need_login: "form[action='login']" },
                        ]
                    });
                    site_map.push({
                        name: "NZB年费影视",
                        label: [
                            { name: "abNZB", link: 'https://www.abnzb.com/search/' + ywm, selector: "#browsetable a.title", selector_need_login: "#modalLogin" },
                            { name: "DOGnzb", link: 'https://dognzb.cr/search?q=' + ywm, selector: "tr.odd a.link", selector_need_login: "#login" },
                            { name: "NZBFind", link: 'https://nzbfinder.ws/search?id=' + ywm, selector: "td.check + td a", selector_need_login: "div.account-form" },
                            { name: "NZBNDX", link: 'https://nzbndx.com/search/' + ywm, selector: "#browsetable a.title", selector_need_login: "#modalLogin" },
                            { name: "NzbNoob", link: 'https://nzbnoob.com/search/' + ywm, selector: "#browsetable a.title", selector_need_login: "#modalLogin" },
                            { name: "NZBSU", link: 'https://nzb.su/search/' + ywm, selector: "#browsetable a.title", selector_need_login: "#modalLogin" },
                        ]
                    });
                    site_map.push({
                        name: "NZB免费影视",
                        label: [
                            { name: "BiNZB", link: 'http://binzb.com/search?q=' + ywm, selector: ".list td .groups" },
                            { name: "Bsearch", link: 'http://binsearch.info/?q=' + ywm, selector: "td span.s" },
                            { name: "FindNZB", link: 'https://findnzb.net/?q=' + ywm, selector: ".results .big" },
                            { name: "FreeNZBs", link: 'https://freenzbs.com/?search%5Btree%5D=cat0_z0_a0&sortdir=ASC&sortby=&search%5Bvalue%5D%5B%5D=Title%3A%3D%3ADEF%3A' + eng_title_clean, selector: "#spots td.title" },
                            { name: "NewzNab", link: 'https://newz69.keagaming.com/search/' + ywm, selector: "#browsetable a.title", selector_need_login: "form[action='login']" },
                            { name: "NZBStar", link: 'https://nzbstars.com/?search%5Btree%5D=cat0_z0_a0&sortdir=ASC&sortby=&search%5Bvalue%5D%5B%5D=Title%3A%3D%3ADEF%3A' + eng_title_clean, selector: "#spots td.title" },
                            { name: "NZBXS", link: 'https://www.nzbxs.com/?search%5Btree%5D=cat0_z0_a0&sortdir=ASC&sortby=&search%5Bvalue%5D%5B%5D=Title%3A%3D%3ADEF%3A' + eng_title_clean, selector: "#spots td.title" },
                            { name: "SpotNZB", link: 'https://spotnzb.xyz/?search%5Btree%5D=cat0_z0_a0&sortdir=ASC&sortby=&search%5Bvalue%5D%5B%5D=Title%3A%3D%3ADEF%3A' + eng_title_clean, selector: "#spots td.title" },
                        ]
                    });
                    site_map.push({
                        name: "PT影视外站",
                        label: [
                            { name: "AR", link: 'https://alpharatio.cc/torrents.php?searchstr=' + ywm, selector: "#torrent_table > tbody > tr:gt(0)" },
                            { name: "AHD", link: 'https://awesome-hd.me/torrents.php?id=' + imdb_id, selector: ".torrent_table", selector_need_login: "#loginform" },
                            { name: "AsiaCine", link: 'https://asiancinema.me/filterTorrents?' + unit3d, selector: "div.table-responsive a.view-torrent" },
                            { name: "AvistaZ", link: 'https://avistaz.to/' + movieright + "?" + avistaz, selector: "div.block div.overlay-container" },
                            { name: "BHD", link: 'https://beyond-hd.me/browse.php?incldead=0&search=' + imdb_id, selector: "table.tb_detail.grey.torrenttable:last > tbody > tr:gt(0)" },
                            { name: "CinemaZ", link: 'https://cinemaz.to/' + movieright + "?" + avistaz, selector: "div.block div.overlay-container" },
                            { name: "Classix", link: 'http://classix-unlimited.co.uk/torrents-search.php?incldead=0&search=' + eng_title, selector: "table.ttable_headinner tr.t-row" },
                            { name: "FileList", link: 'https://filelist.ro/browse.php?searchin=3&search=' + imdb_id, selector: "div.torrentrow a[data-html='true']" },
                            { name: "HDB", link: 'https://hdbits.org/browse.php?&imdb=' + imdb_id, selector: "#torrent-list", selector_need_login: "a[href='/recover.php']" },
                            { name: "HDF", link: 'https://hdf.world/torrents.php?searchstr=' + ywm, selector: "#torrent_table > tbody > tr:gt(0)" },
                            { name: "HDME", link: 'http://hdme.eu/browse.php?incldead=1&blah=1&search=' + imdb_id, selector: "table:nth-child(13) > tbody > tr" },
                            { name: "HDMonkey", link: 'https://hdmonkey.org/torrents-search.php?incldead=0&search=' + ywm, selector: "table.ttable_headinner > tbody > tr:gt(0)" },
                            { name: "HDS", link: 'https://hd-space.org/index.php?page=torrents&active=1&options=2&search=' + imdb_id, selector: "table.lista:last > tbody > tr:gt(0)", selector_need_login: "form[name='login']" },
                            { name: "HDT", link: 'https://hd-torrents.org/torrents.php?active=1&options=2&search=' + imdb_id, selector: "table.mainblockcontenttt b", selector_need_login: "form[name='login']" },
                            { name: "IPT", link: 'https://iptorrents.com/t?qf=all&q=' + imdb_id, selector: "#torrents td.ac" },
                            { name: "MTV", link: 'https://www.morethan.tv/torrents.php?searchstr=' + eng_title_clean, selector: "table.torrent_table > tbody > tr:gt(0)" },
                            { name: "PHD", link: 'https://privatehd.to/' + movieright + "?" + avistaz, selector: "div.block div.overlay-container" },
                            { name: "PTF", link: 'http://ptfiles.net/browse.php?incldead=0&title=0&search=' + ywm, selector: "#tortable > tbody > tr.rowhead:gt(0)" },
                            { name: "PTP", link: 'https://passthepopcorn.me/torrents.php?searchstr=' + imdb_id, selector: '#torrent-table tr.group_torrent.group_torrent_header:gt(0)', selector_need_login: "#loginform" },
                            { name: "RTF", link: 'https://retroflix.club/torrents1.php?incldead=1&spstate=0&inclbookmarked=0&search_area=4&search_mode=0&search=' + imdb_id, selector: "td table.torrentname" },
                            { name: "SC", link: 'https://secret-cinema.pw/torrents.php?cataloguenumber=' + imdb_id, selector: "div.torrent_card" },
                            { name: "SDB", link: 'http://sdbits.org/browse.php?incldead=0&imdb=' + imdb_id, selector: "#torrent-list tr.light" },
                            { name: "Speed", link: 'https://speed.cd/browse.php?d=on&search=' + imdb_id, selector: "div.boxContent > table:first >tbody > tr:gt(0)" },
                            { name: "TD", link: 'https://www.torrentday.com/t?q=' + imdb_id, selector: "#torrentTable td.torrentNameInfo" },
                            { name: "TS", link: 'https://www.torrentseeds.org/browse.php?searchin=title&incldead=0&search=%22' + eng_title + year + '%22', selector: "table.table.table-bordered > tbody > tr.browse_color:gt(0)" },
                            { name: "TT", link: 'https://revolutiontt.me/browse.php?search=' + imdb_id, selector: "table#torrents-table > tbody > tr:gt(0)" },
                            { name: "TL", type: "json", link: "https://www.torrentleech.org/torrents/browse/index/query/" + eng_title + nian, ajax: "https://www.torrentleech.org/torrents/browse/list/query/" + eng_title + year, selector: "numFound > 0" },
                            { name: "UHD", link: 'https://uhdbits.org/torrents.php?searchstr=' + imdb_id, selector: "table.torrent_table > tbody > tr.group" },
                        ]
                    });
                }
                if (is_india || is_pakistan) {
                    site_map.push({
                        name: "PT印度电影站",
                        label: [
                            { name: "BwT", link: "https://bwtorrents.tv/index.php?blah=0&cat=0&incldead=1&search=" + ywm, selector: "table.pager + table tr.browse" },
                            { name: "Hon3yHD", link: "https://hon3yhd.com/browse.php?searchin=title&incldead=0&search=" + eng_title, selector: "table tr.tt" },
                            { name: 'Desitor', method: "post", type: "json", link: 'https://desitorrents.tv/#search_' + ywm, ajax: 'https://desitorrents.tv/ajax.php?action=search_torrent_cats', data: `selected_group=&search_username=&selected_sorting=relevance&search_string=${ywm}`, headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8" }, selector: 'torrent_html.length > 0' },
                        ]
                    });
                }
                site_map.push({
                    name: "PT影视原声",
                    label: [
                        { name: "DicMusic", link: 'https://dicmusic.club/torrents.php?notnewword=1&searchstr=' + unititle, selector: "td.td_info.big_info" },
                        { name: "OpenCD", link: 'https://open.cd/torrents.php?incldead=1&search_area=0&notnewword=1&search=' + unititle, selector: "table.torrents:last > tbody > tr:gt(0)" },
                        { name: "JPOP", link: 'https://jpopsuki.eu/torrents.php?searchstr=' + eng_title, selector: "#torrent_table > tbody > tr:gt(0)" },
                        { name: "Orpheus", link: 'https://orpheus.network/torrents.php?searchstr=' + eng_title, selector: "#torrent_table:last > tbody > tr.group_torrent:gt(0)" },
                        { name: "Red", link: 'https://redacted.ch/torrents.php?searchstr=' + eng_title, selector: "#torrent_table > tbody > tr.group_torrent:gt(0)" },
                        { name: "Waffles", link: 'https://waffles.ch/browse.php?q=' + eng_title, selector: "#browsetable:last > tbody > tr:gt(0)" },
                    ]
                });
                site_map.push({
                    name: "终生会员论坛",
                    label: [
                        { name: "古哥论坛", link: 'http://www.gudage.cc/search.php?mod=forum&searchsubmit=yes&srchtxt=' + gunititle, selector: "div.tl li.pbw" },
                        { name: "抱书吧", link: 'http://www.baoshu8.com/searcher.php?type=thread&keyword=' + gunititle, selector: "div.dlA dl" },
                        { name: "国配影迷", link: 'https://club.ccmnn.com/search.php?mod=forum&searchsubmit=yes&srchtxt=' + gunititle, selector: "div.tl li.pbw" },
                        { name: "慢慢游影", link: 'https://www.mmybt.com/search.php?mod=forum&searchsubmit=yes&srchtxt=' + unititle, selector: "div.tl li.pbw", selector_need_login: "#messagelogin" },
                        { name: "盘乐网影", link: 'http://www.haopanyou.com/search.php?mod=forum&searchsubmit=yes&srchtxt=' + unititle, selector: "div.tl li.pbw", selector_need_login: "#ls_username" },
                        { name: "印度电影", link: 'http://www.indmi.com/search.php?mod=forum&searchsubmit=yes&srchtxt=' + unititle, selector: "div.tl li.pbw" },
                        { name: "云中漫步", link: 'https://www.yunzmb.com/search.php?mod=forum&searchsubmit=yes&srchtxt=' + gunititle, selector: "div.tl li.pbw" },
                    ]
                });
                site_map.push({
                    name: "影视论坛资源",
                    label: [
                        { name: "网盘分享吧", link: 'http://www.wpfx8.com/search.php?mod=forum&searchsubmit=yes&srchtxt=' + unititle, selector: "div.tl li.pbw", selector_need_login: "#messagelogin" },
                        { name: "深影论坛", link: 'http://forum.shinybbs.vip/search.php?mod=forum&searchsubmit=yes&srchtxt=' + gunititle, selector: "div.tl li.pbw", selector_need_login: "#messagelogin" },
                    ]
                });
                if (!(is_mandarine) || (is_mandarine && is_otherlan)) {
                    site_map.push({
                        name: "PT影视字幕",
                        label: [
                            { name: "BTSchool®", link: 'http://pt.btschool.club/subtitles.php?notnewword=1&search=' + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "BeiTai®", link: "https://www.beitai.pt/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "CHDBits®", link: "https://chdbits.co/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table:last > tbody > tr:gt(1)" },
                            { name: "FRDS®", link: "http://pt.keepfrds.com/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "GHTT®", link: 'https://www.hitpt.com/subtitles.php?notnewword=1&search=' + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "Hares®", link: 'https://club.hares.top/subtitles.php?notnewword=1&search=' + ptzimu, selector: "table:last > tbody > tr:gt(1)" },
                            { name: "HD4FANS®", link: 'https://pt.hd4fans.org/subtitles.php?notnewword=1&search=' + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "HDArea®", link: 'https://www.hdarea.co/subtitles.php?notnewword=1&search=' + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)", selector_need_login: "h1 span:contains('Checking your browser before accessing')" },
                            { name: "HDChina®", link: "https://hdchina.org/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table.uploaded_sub_list > tbody > tr:gt(1)" },
                            { name: "HDCity®", link: "https://hdcity.city/subtitles?notnewword=1&search=" + ptzimu, selector: "center > div:nth-child(1) > table > tbody > tr:nth-child(2)" },
                            { name: "HDHome®", link: "https://hdhome.org/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table:last > tbody > tr:gt(1)" },
                            { name: "HDSky®", link: "https://hdsky.me/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table:last > tbody > tr:gt(1)" },
                            { name: "HDTime®", link: "https://hdtime.org/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table[width='100%'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr" },
                            { name: "HDU®", link: "http://pt.upxin.net/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "JoyHD®", link: "https://www.joyhd.net/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "LemonHD®", link: 'https://lemonhd.org/subtitles.php?notnewword=1&search=' + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "MTeam®", link: "https://kp.m-team.cc/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table.table-subtitle-list:last > tbody > tr" },
                            //{ name: "NPUBITS®", link: "https://npupt.com/subtitles.php?notnewword=1&search=" + ptzimu, selector: "#main > table > tbody > tr:nth-child(2)" },
                            { name: "NYPT®", link: "https://nanyangpt.com/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "OurBits®", link: "https://ourbits.club/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "PTHOME®", link: 'https://www.pthome.net/subtitles.php?notnewword=1&search=' + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "PT之友®", link: 'https://pterclub.com/subtitles.php?notnewword=1&search=' + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "SJTU®", link: "https://pt.sjtu.edu.cn/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "Spring®", link: 'https://springsunday.net/subtitles.php?notnewword=1&search=' + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "TCCF®", link: "https://et8.org/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "TJUPT®", link: "https://www.tjupt.org/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "TLFBits®", link: "http://pt.eastgame.org/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                            { name: "U2®", link: "https://u2.dmhy.org/subtitles.php?notnewword=1&search=" + ptzimu, selector: "table[width='940'][border='1'][cellspacing='0'][cellpadding='5'] > tbody > tr:nth-child(2)" },
                        ]
                    });
                }
            }

            if (!(is_mandarine) || (is_mandarine && is_otherlan)) {
                site_map.push({
                    name: "精准中文字幕",
                    label: [
                        { name: 'r3sub', link: 'https://r3sub.com/search.php?s=' + dbzw, selector: "div.col-sm-8.col-md-9.col-lg-8 div.movie.movie--preview.ddd" },
                        { name: 'OpenSub', link: 'https://www.opensubtitles.org/zh/search/sublanguageid-chi,zht,zhe,eng/imdbid-' + imdb_id, selector: "#search_results tr.change", selector_need_login: "#recaptcha2" },
                    ]
                });
            }
            if (!(is_mandarine) || (is_mandarine && is_otherlan)) {
                site_map.push({
                    name: "中文影视字幕",
                    label: [
                        { name: 'A4k字幕', link: 'https://www.a4k.net/search?term=' + unititle, selector: "h3 a" },
                        { name: 'Sub HD', link: 'https://subhd.tv/search/' + unititle, selector: ".position-relative .float-start" },
                        { name: '伪射手', link: 'http://assrt.net/sub/?searchword=' + unititle, selector: "#resultsdiv a.introtitle" },
                        { name: '中文字幕网', link: 'http://www.zimuzimu.com/so_zimu.php?title=' + unititle, selector: "table.sublist a.othersub" },
                    ]
                });
            }
            if (!(is_mandarine) || (is_mandarine && is_otherlan)) {
                site_map.push({
                    name: "英文影视字幕",
                    label: [
                        { name: 'Addic7ed', link: 'http://www.addic7ed.com/srch.php?search=' + eng_title_clean + year, selector: "table.tabel tr" },
                        { name: 'iSubtitles', link: 'https://isubtitles.info/search?kwd=' + ywm, selector: "div.movie-list-info h3" },
                        { name: 'Podnapisi', link: 'https://www.podnapisi.net/zh/subtitles/search/?language=zh&language=en&keywords=' + eng_title_clean + '&' + year + '-' + year, selector: "table tr.subtitle-entry" },
                        { name: 'Subscene', link: 'https://subscene.com/subtitles/title?q=' + eng_title_clean, selector: "div.search-result div.title", selector_need_login: "h1 span:contains('Checking your browser')" },
                        { name: 'TVsubtitles', link: 'http://www.tvsubtitles.net/search.php?q=' + eng_title_clean, selector: "div.left_articles li" },
                        { name: 'YIFY', link: 'http://www.yifysubtitles.com/search?q=' + eng_title_clean, selector: "div.col-sm-12 div.col-xs-12" },
                    ]
                });
            }
            site_map.push({
                name: "影视精准匹配",
                label: [
                    { name: 'BD影视', link: 'https://www.bd-film.cc/search.jspx?q=' + dbzw, selector: '#content_list li.list-item' },
                    { name: 'RARBG', link: 'https://rarbgprx.org/torrents.php?search=' + jingzhun, selector: 'table.lista2t tr.lista2' },
                    { name: 'TorGal', link: 'https://tgx.rs/torrents.php?search=' + jingzhun, selector: '#click' },
                    { name: 'Zooqle', link: 'https://zooqle.com/search?q=' + jingzhun, selector: 'div.panel-body a.small' },
                    { name: '爱笑聚', link: 'https://www.axjbd.com/app-index-run?app=search&keywords=' + dbzw, /*csrf: { name: 'csrf_token', update: "link" },*/ selector: 'div.search_content div.text' },
                    { name: '比特大雄', link: 'https://www.btdx8.com/?s=' + dbzw, selector: '#content div.post.clearfix' },
                    { name: '就爱那片', method: "post", link: 'http://www.ainapian.com/index.php?s=vod-search&wd=' + dbzw, data: `wd=${unititle}`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: 'div.sortcon div.minfo' },
                    { name: '片源网', link: 'http://pianyuan.org/search?q=' + dbzw, selector: 'div.row ul.detail' },
                    { name: '迅雷影天堂', link: 'https://www.xl720.com/?s=' + dbzw, selector: '#content h3.entry-title' },
                    { name: '音范丝', link: 'http://www.yinfans.me/?s=' + dbzw, selector: '#post_container div.article' },
                    { name: '中国高清网', link: 'http://gaoqing.la/?s=' + dbzw, selector: 'div.mainleft div.thumbnail' },
                ]
            });
            site_map.push({
                name: "阿里云盘搜索",
                label: [
                    { name: "小雅", link: 'http://alist.xiaoya.pro/search?type=video&box=' + unititle, },
                    { name: 'T-REX', link: 'https://t-rex.tzfile.com/?s=' + unititle, selector: '.entry-title', selector_need_login: "h1 span:contains('Checking your browser')" },
                    { name: '阿里小站', link: 'https://newxiaozhan.com/search.php?mod=forum&orderby=dateline&searchsubmit=yes&srchtxt=' + unititle, selector: 'div.tl li.pbw' },
                    { name: '分派电影', link: 'https://ifenpaidy.com/page/' + unititle, selector: '.page-title' },
                    { name: '网盘小站', link: 'https://wpxz.org/?q=' + unititle, ajax: "https://wpxz.org/api/discussions?page%5Blimit%5D=3&include=mostRelevantPost&filter%5Bq%5D=" + unititle, type: "json", selector: 'data.length > 0' },
                    { name: '云盘资源网', link: 'https://www.yunpanziyuan.com/fontsearch.htm?fontname=' + unititle, selector: '.media.thread.tap' },
                ]
            });
            if (is_series) {
                site_map.push({
                    name: "网盘搜剧集",
                    label: [
                        { name: 'Pan58剧集', link: 'http://www.pan58.com/s?wd=' + unititle + '&s=1&t=0&p=1', selector: `.filetext p.fname:contains(${unititle})` },
                        { name: '毕方铺', link: 'https://www.iizhi.cn/resource/search/searchtype=0&searchway=1&' + unititle, selector: '.main-info h1' },
                        { name: '小猪快盘', link: 'https://www.xiaozhukuaipan.com/s/search?q=' + unititle + '&currentPage=1&f=6', selector: `h4 a:contains(${unititle})` },
                    ]
                });
            }
            if (is_movie) {
                site_map.push({
                    name: "网盘搜电影",
                    label: [
                        { name: 'Pan58电影', link: 'http://www.pan58.com/s?wd=' + unititle + '&s=2&t=0&p=1', selector: `.filetext p.fname:contains(${unititle})` },
                        { name: '小昭来了影', link: 'https://www.xiaozhaolaila.com/s/search?q=' + unititle + '&currentPage=1&s=down&f=1', selector: `h4 a:contains(${unititle})` },
                    ]
                });
            }
            /** if (has_imdb || is_ywm) {
                site_map.push({
                    name: "国外网盘精准",
                    label: [
                        { name: 'BestMovie✇', link: 'https://www.best-moviez.ws/?s=' + jingzhun, selector: '#content h1.entry-title', selector_need_login: "h1 span:contains('Checking your browser')" },
                        { name: 'DDLWare✇', link: 'https://ddl-warez.to/?search=' + jingzhun, selector: 'table.table-condensed td.no_overflow', selector_need_login: "h1 span:contains('Checking your browser')" },
                        { name: 'DL4ALL✇', link: 'http://dl4all.xyz/?do=search&subaction=search&story=' + jingzhun, selector: 'span.category h2', selector_need_login: "h1 span:contains('Checking your browser')" },
                        { name: 'Downtr✇', link: 'https://downtr.cc/?do=search&subaction=search&story=' + jingzhun, selector: '#dle-content div.title', selector_need_login: "h1 span:contains('Checking your browser')" },
                        { name: 'FilmSoft✇', link: 'http://filmsofts.com/?do=search&subaction=search&story=' + jingzhun, selector: '#dle-content div.story', selector_need_login: "h1 span:contains('Checking your browser')" },
                        { name: 'Freshwap✇', link: 'http://www.freshwap.cc/?do=search&subaction=search&story=' + jingzhun, selector: '#dle-content div.maincont', selector_need_login: "h1 span:contains('Checking your browser')" },
                        { name: 'MovieWBB✇', link: 'http://movieswbb.net/?s=' + jingzhun, selector: 'div.content.blog div.blogpostcategory', selector_need_login: "h1 span:contains('Checking your browser')" },
                        { name: 'OneDDL✇', link: 'https://oneddl.org/?do=search&subaction=search&story=' + jingzhun, selector: '#dle-content div.con', selector_need_login: "h1 span:contains('Checking your browser')" },
                        { name: 'WarezSer✇', link: 'http://warez-serbia.com/index.php?do=search&subaction=search&story=' + jingzhun, selector: '#dle-content div.post-info', selector_need_login: "h1 span:contains('Checking your browser')" },
                        { name: 'Win7DL✇', link: 'https://win7dl.org/?do=search&subaction=search&story=' + jingzhun, selector: '#dle-content td.block_head_2', selector_need_login: "h1 span:contains('Checking your browser')" },
                    ]
                });
            } **/
            site_map.push({
                name: "在线正版中文",
                label: [
                    { name: '爱奇艺视频', link: 'https://so.iqiyi.com/so/q_' + unititle, selector: "div.mod_result span.play_source" },
                    { name: '哔哩哔哩', link: 'https://search.bilibili.com/all?keyword=' + unititle, selector: 'span.bangumi-label+a' },
                    { name: '乐视视频', link: 'http://so.le.com/s?wd=' + unititle, selector: `h1 > a.j-baidu-a[title*='${unititle}']` },
                    { name: '芒果TV', link: 'https://so.mgtv.com/so/k-' + unititle, selector: 'div.so-result-info.clearfix span.label' },
                    { name: '搜狐视频', link: 'https://so.tv.sohu.com/mts?wd=' + unititle, selector: 'div.wrap.cfix div.cfix.resource' },
                    { name: '腾讯视频', link: 'https://v.qq.com/x/search/?q=' + unititle, selector: 'div.wrapper_main div._infos' },
                    { name: '优酷视频', link: 'https://www.soku.com/nt/search/q_' + unititle, selector: 'div.s_intr span.intr_area.c_main' },
                ]
            });
            site_map.push({
                name: "在线正版英文",
                label: [
                    { name: 'Amazon', link: 'https://instantwatcher.com/a/search?content_type=1+2&source=1+2+3&q=' + eng_title_clean, selector: `span.title a.title-link:contains(${eng_title_clean})` },
                    { name: 'Netflix', link: 'https://unogs.com/?q=' + eng_title_clean, ajax: 'https://flixable.com/?s=' + eng_title_clean, selector: ".card-header.card-header-image" },
                ]
            });
            site_map.push({
                name: "在线中文影视",
                label: [
                    { name: '7080影视', link: 'https://7080.wang/so.html?mode=search&wd=' + unititle, ajax: "https://www.39kan.com/api.php/provide/vod/?ac=detail&wd=" + unititle, type: "json", selector: " list.length > 0" },
                ]
            });
            if (has_entitle) {
                site_map.push({
                    name: "在线英文影视",
                    label: [
                        { name: 'UniStream', link: 'https://uniquestream.net/?s=' + eng_title_clean, selector: 'div.result-item div.details' },
                    ]
                });
            }
            if (is_anime) {
                site_map.push({
                    name: "在线动漫视频",
                    label: [
                        { name: '9ANIME', link: 'https://9anime.to/search?keyword=' + eng_title, selector: "div.film-list a.name" },
                        { name: '爱看番', link: 'http://www.ikanfan.com/search/?wd=' + unititle, selector: '#listvod div.d-info' },
                    ]
                });
            }
            if (is_anime) {
                site_map.push({
                    name: "动漫国内网站",
                    label: [
                        { name: 'ACG.RIP', link: 'https://acg.rip/?term=' + unititle, selector: 'tbody tr' },
                        { name: 'ACG搜', link: 'https://www.36dm.club/search.php?keyword=' + unititle, selector: 'tbody span.bts_1' },
                        { name: 'Mikan', link: 'https://mikanani.me/Home/Search?searchstr=' + unititle, selector: 'table.table.table-striped.tbl-border.fadeIn a.magnet-link-wrap' },
                        { name: 'MioBT', link: 'http://www.miobt.com/search.php?keyword=' + unititle, selector: '#data_list tr[class*=alt]' },
                        { name: 'VCB-S', link: 'https://vcb-s.com/?s=' + unititle, selector: '#article-list div.title-article' },
                        { name: '爱恋动漫', link: 'http://www.kisssub.org/search.php?keyword=' + unititle, selector: 'tbody span.bts_1' },
                        { name: '动漫花园', link: 'https://share.dmhy.org/topics/list?keyword=' + unititle, selector: 'tbody span.btl_1' },
                        { name: '兜兜动漫网', link: 'http://www.doudoudm.com/Home/Index/search.html?searchText=' + unititle, selector: '#some_drama span.play_some' },
                        { name: '漫喵动漫', link: 'http://www.comicat.org/search.php?keyword=' + unititle, selector: '#data_list tr' },
                        { name: '漫相随', link: 'http://fodm.net/search.asp?searchword=' + gunititle, selector: 'div.page_content div.intro' },
                        { name: "萌番组", method: "post", type: "json", link: "https://bangumi.moe/search/title#search_" + unititle, ajax: "https://bangumi.moe/api/v2/torrent/search", data: `{"query":"${unititle}"}`, headers: { "Content-Type": "text/plain;charset=UTF-8" }, selector: "count > 0" },
                        { name: '末日动漫', link: 'https://share.acgnx.se/search.php?sort_id=0&keyword=' + unititle, selector: '#listTable tr[class*=alt]' },
                        { name: '魔法少女', link: 'https://www.mahou-shoujo.moe/?s=' + this_title, selector: '#main div.entry-summary' },
                        { name: '怡萱动漫', link: 'http://www.yxdm.tv/search.html?title=' + unititle, selector: 'div.main p.stars1' },
                    ]
                });
            }

            if (is_anime && eng_title.trim().length > 0) {
                site_map.push({
                    name: "动漫国外网站",
                    label: [
                        { name: 'AniDex', link: 'https://anidex.info/?q=' + eng_title, selector: 'div.table-responsive tr' },
                        { name: 'AniRena', link: 'https://www.anirena.com/?s=' + eng_title, selector: '#content table' },
                        { name: 'AniTosho', link: 'https://animetosho.org/search?q=' + eng_title, selector: '#content div.home_list_entry' },
                        { name: 'Nyaa', link: 'https://nyaa.si/?q=' + eng_title, selector: 'div.table-responsive tr.default' },
                        { name: 'ニャパンツ', link: 'https://nyaa.pantsu.cat/search?c=_&q=' + eng_title, selector: '#torrentListResults tr.torrent-info' },
                        { name: '东京図书馆', link: 'https://www.tokyotosho.info/search.php?terms=' + eng_title, selector: 'table.listing td.desc-top' },
                    ]
                });
            }
            if (is_series && is_europe) {
                site_map.push({
                    name: "欧美剧集下载",
                    label: [
                        { name: 'BT美剧', link: 'http://www.btmeiju.com/ustv_search.htm?title=' + unititle, selector: '#_container div.comm_box' },
                        { name: 'EZTV', link: 'https://eztv.ag/search/' + ywm.replace(/S\d+$/g,''), selector: `td.forum_thread_post > a[title*='${ywm.replace(/S\d+$/g,'')}']` },
                        { name: 'KPPT', link: 'http://www.kppt.cc/search.php?q=' + unititle, selector: 'div.search span.SearchAlias' },
                        { name: '爱美剧', link: 'https://www.meiju22.com/search.php?searchword=' + unititle, selector: 'div.head h3' },
                        { name: '每日美剧', link: 'http://www.meirimeiju.com/search?words=' + unititle, selector: 'div.container div.movie-title' },
                        { name: '美剧迷', link: 'http://www.meijumi.vip/index.php?s=' + unititle + ' 下载', selector: `h2.entry-title > a:contains(${unititle})` },
                        { name: '美剧天堂', link: 'https://www.meijutt.tv/search/index.asp?searchword=' + gunititle, selector: 'div.list3_cn_box ul.list_20' },
                        { name: '人人影视', link: 'http://www.zmz2019.com/search?type=resource&keyword=' + unititle, selector: "div.search-result > ul > li" },
                        //{ name: '人人美剧', link: 'http://www.yyetss.com/Search/index/s_keys/' + unititle, selector: 'div.row div.col-xs-3' },
                    ]
                });
            }
            if (is_series && is_japan && !is_anime) {
                site_map.push({
                    name: "日剧资源下载",
                    label: [
                        { name: '91日剧', link: 'http://www.wwmulu.com/?s=' + unititle, selector: `h2.entry-title > a:contains(${unititle})` },
                        { name: "东京不够热", method: "post", link: "http://www.tokyonothot.com/search.php?mod=portal", data: `srchtxt=${gunititle}&searchsubmit=yes`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: "div.tl li.pbw" },
                        { name: '花译工坊', link: 'https://discuss.huayiwork.com/?q=' + unititle, ajax: "https://discuss.huayiwork.com/api/xun/discussions?include=page%5Blimit%5D=3&include=mostRelevantPost&filter%5Bq%5D=" + unititle, type: "json", selector: 'data.length > 0' },
                        { name: '心动日剧', link: 'http://www.doki8.com/?s=' + unititle, selector: `h2.post-box-title > a:contains(${unititle})` },
                        { name: '隐社', link: 'http://www.hideystudio.com/drama/' + release_year + drama_season + '.html', selector: `td > span.titles:contains(${unititle})` },
                        { name: '猪猪日部落', link: 'http://www.zzrbl.com/?s=' + unititle, selector: 'div.section_body li' },
                        { name: '追新番', method: "post", link: 'http://www.zhuixinfan.com/search.php?searchsubmit=yes', data: `mod=tvplay&formhash=453fc7da&srchtype=title&srhfid=0&srhlocality=main%3A%3Aindex&srchtxt=${unititle}&searchsubmit=true`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: '#wp td.td2' },
                    ]
                });
            }
            if (is_series && is_korea && !is_anime) {
                site_map.push({
                    name: "韩剧资源下载",
                    label: [
                        { name: '韩饭网', link: 'http://www.hanfan.cc/?s=下载 ' + unititle, selector: 'div.content p.meta' },
                        { name: '韩剧迷', link: 'http://www.aioio.cn/?s=下载 ' + unititle, selector: 'div.content p.meta' },
                        { name: '韩流韩剧网', link: 'http://www.hlhanju.com/index.php?s=vod-search-wd-' + unititle, selector: '#find-focus div.play-txt' },
                        { name: '韩迷', link: "http://www.hanmi520.com/search.php?mod=forum&searchsubmit=yes&srchtxt=" +unititle, selector: "div.tl li.pbw" },
                    ]
                });
            }
            if (is_series && is_thai && !is_anime) {
                site_map.push({
                    name: "泰剧资源下载",
                    label: [
                        { name: '97泰剧网', link: 'http://www.97taiju.com/index.php?s=vod-search&wd=' + unititle, selector: '#vodlist dd.title' },
                        { name: '泰剧资料馆', link: 'http://www.taijuzlg.com/?s=泰剧下载 ' + unititle, selector: '#main li.entry-title' },
                    ]
                });
            }
            if (is_document) {
                site_map.push({
                    name: "纪录片下载站",
                    label: [
                        { name: '盗火纪录片', link: 'http://www.daofire.com/search/titlesearch?keyword=' + unititle, selector: 'div.videos div.post_title' },
                        { name: '纪录片天地', link: 'https://www.bing.com/search?q=site%3Awww.jlpcn.net+intitle%3A' + unititle, selector: '#b_content div.b_title' },
                        { name: '熊猫盘纪录', link: 'http://xiongmaopan.com/search/' + unititle, selector: `h2 > a[title*='${unititle}']` },
                    ]
                });
            }
            site_map.push({
                name: "电影资源下载",
                label: [
                    { name: '4K电影', link: 'https://4k-m.com/m/s.aspx?s=' + unititle, selector: 'div.list-pic div.txt' },
                    { name: '19影视', link: 'https://www.19kan.com/vodsearch.html?wd=' + unititle, selector: 'h1 .fed-text-green.fed-text-bold' },
                    { name: '66影视网', method: "post", link: 'https://www.66e.cc/e/search/index.php', data: `show=title%2Csmalltext&tempid=1&tbname=Article&keyboard=${gunititle}&submit=`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: "div.listBox li" },
                    { name: '6V电影网', method: "post", link: 'http://www.6vhao.tv/e/search/index.php', data: `show=title%2Csmalltext&tempid=1&tbname=Article&keyboard=${gunititle}&Submit22=%E6%90%9C%E7%B4%A2`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: "div.listBox li" },
                    { name: 'LOL电影', link: 'http://www.993dy.com/index.php?m=vod-search&wd=' + unititle, selector: '.movielist h5' },
                    { name: 'MP4电影', link: 'http://www.domp4.cc/search/' + unititle + '-1.html', selector: `h2 a:contains(${unititle})` },
                    { name: 'SOZMZ', link: 'https://v.dsb.ink/#/#search_' + unititle, ajax: "https://v.dsb.ink/getinfo.php?page=1&search=" + unititle, type: "json", selector: 'count > 0' },
                    { name: '哔嘀影视', link: 'https://www.btbdys.com/search/' + unititle, selector: 'a.search-movie-title', selector_need_login: ".alert.alert-success p:contains('需要输入验证码')" },
                    { name: '比特影视', link: 'https://www.bteye.com/search/' + unititle, selector: '#main div.item' },
                    { name: '电影港', method: "post", link: 'https://www.dygang.cc/e/search/index.php', data: `tempid=1&tbname=article&keyboard=${gunititle}&show=title%2Csmalltext&Submit=%CB%D1%CB%F7`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: "table[width='100%'][border='0'][cellspacing='0'][cellpadding='0'] a.classlinkclass" },
                    { name: '电影天堂', method: "post", link: 'https://www.dy2018.com/e/search/index.php', data: `show=title&keyboard=${gunititle}`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: 'b a.ulink' },
                    { name: '高清888', link: 'https://www.gaoqing888.com/search?kw=' + unititle, selector: 'div.wp-content div.video-row' },
                    { name: '高清电台', link: 'https://gaoqing.fm/s.php?q=' + unititle, selector: '#result1 div.row' },
                    //{ name: '狗哥电影', method: "post", link: 'https://www.gghd.cc/index.php?m=vod-search=wd=' +unititle, csrf: { name: "csrf_token", update: "link" }, headers: { "Content-Type": "application/x-www-form-urlencoded" }, ajax: "https://www.gghd.cc/index.php?m=vod-search=wd=" + unititle, headers: { "Content-Type": "application/x-www-form-urlencoded" }, selector: 'ul.topic-list div.index-topic-info' },
                    { name: '好恐怖', method: "post", link: 'https://s.haokongbu1.com/e/search/index.php', data: `show=title&keyboard=${unititle}`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: '.channel-content li' },
                    { name: "两个BT", link: 'https://www.bttwo.com/xssearch?q=' + unititle, selector: 'div.mi_cont h3.dytit' },
                    { name: "皮皮虾资源", link: 'https://ppxzy.cc/?s=' + unititle, selector: `.entry-title a:contains(${unititle})` },
                    { name: '新6V电影', method: "post", link: 'https://www.66s.cc/e/search/index.php', data: `show=title&tempid=1&tbname=article&mid=1&dopost=search&submit=&keyboard=${unititle}`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: '#post_container div.entry_post' },
                    { name: '迅播影院', link: 'http://www.22tu.tv/vodsearch/-------------/?wd=' + unititle + '&submit=%E6%90%9C+%E7%B4%A2', selector: 'ul.mlist div.info' },
                    { name: '迅雷影天堂', link: 'https://www.xl720.com/?s=' + unititle, selector: `h3 > a[title*='${unititle}']` },
                    { name: '悠悠MP4', link: 'https://www.uump4.net/search-' + uunititle + '.htm', selector: 'div.card-body2 div.dateline' },
                ]
            });
            site_map.push({
                name: "BT国内网站",
                label: [
                    { name: 'BT部落', link: 'http://www.btbuluo.net/s/' + unititle + '.html', selector: `h2 a:contains(${unititle})` },
                    { name: 'BT之家', link: 'https://www.btbtt12.com/search-index-keyword-' + unititle + '.htm', selector: '#threadlist table' },
                    { name: '查片源', link: 'https://www.chapianyuan.com/?keyword=' + unititle, selector: '.block-list li' },
                    // { name: 'MVCAT', link: 'http://www.mvcat.com/search/?type=Title,subTitle,Tags&word=' + unititle, selector: 'h3.title' },
                ]
            });
            if (has_imdb) {
                site_map.push({
                    name: "BT国外网站",
                    label: [
                        { name: '1337X', link: 'https://www.1337x.to/search/' + ywm + '/1/', selector: 'table.table-list.table.table-responsive.table-striped td.coll-1.name' },
                        //{ name: 'iDope', method: "post", link: 'https://idope.xyz/search-site/', data:`q=${ywm}&x=0&y=0`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: 'div.container div.opt-text-w3layouts' },
                        { name: 'Lime', link: 'https://www.limetorrents.to/search/all/' + ywm, selector: 'table.table2 div.tt-name' },
                        { name: 'Rutrack影', link: 'http://rutracker.org/forum/search_cse.php?q=' + ywm, ajax: `https://www.google.com/search?q=allintitle:+${ywm}+site:rutracker.org`,selector: `a > h3:contains(${eng_title})` },
                        { name: 'TorLock', link: 'https://www.torlock2.com/all/torrents/' + ywm.replace(/ /g, "-") + '.html', selector: 'table.table.table-striped.table-bordered.table-hover.table-condensed td.td' },
                        { name: 'YTS', link: 'https://yts.am/browse-movies/' + eng_title, selector: 'div.row div.browse-movie-bottom' },
                        { name: 'Кинозал', link: 'http://kinozal.tv/browse.php?s=' + ywm, selector: 'table.t_peer.w100p td.nam' },
                        { name: '海盗湾', link: 'https://piratebay.live/search/' + ywm, selector: '#searchResult div.detName' },
                    ]
                });
            }
        } else if (location.host === "book.douban.com") {
            let title = $('#wrapper > h1 > span')[0].textContent.replace(/[:\(].*$/, "");
            let original_anchor = $('#info span.pl:contains("原作名")');
            let original = original_anchor[0] ? fetch_anchor(original_anchor) : '';
            let title_eng = title.match(/([a-zA-Z :,\(\)])+/);
            let original_eng = original.match(/([a-zA-Z :,\(\)])+/);
            let ywm = "";
            if (title_eng) {
                ywm = title;
            } else if (original_eng) {
                ywm = original.replace(/[:\(].*$/, "");
            }
            let has_ywm = title_eng + original_eng;
            let stitle = ywm.toLowerCase().replace(/ /g, "-");
            let is_writer = $('#info span.pl:contains("作者")').length > 0;
            let writer = is_writer ? ' ' + $('#info span.pl:contains("作者")')[0].nextSibling.nextSibling.textContent.replace(/\[[^\]]+\]/g, '').replace(/（[^）]+）/g, '').replace(/^\s{1,}/g, '') : '';
            let gtitle = _encodeToGb2312(title, true);
            let ptitle = encodeURI(title).replace(/%/g, "%25");
            let isbn_anchor = $('#info span.pl:contains("ISBN")');
            let isbn = isbn_anchor[0] ? fetch_anchor(isbn_anchor) : '';

            // 比较时无视英文名大小写
            jQuery.expr[':'].Contains = function(a, i, m) {
                return jQuery(a).text().toUpperCase().indexOf(m[3].toUpperCase()) >= 0;
            };

            function isbn13to10(str) {
                //ISBN 10位和13位码互相转换
                var s;
                var c;
                var checkDigit = 0;
                var result = "";
                s = str.substring(3,str.length);
                for (let i = 10; i > 1; i-- ) {
                    c = s.charAt(10 - i);
                    checkDigit += (c - 0) * i;
                    result += c;
                }
                checkDigit = (11 - (checkDigit % 11)) % 11;
                result += checkDigit == 10 ? 'X' : (checkDigit + "");
                return ( result );
            }

            let isbn10 = isbn13to10 (isbn);

            // 当前只对有isbn号的书籍开启中栏评分增强
            if (isbn) {
                let rating_more_hit = false;
                $("div#interest_sectl").append(`<div class='rating_wrap clearbox' id='loading_more_rate'>加载第三方评价信息中.......</div>
                <div class="rating_wrap clearbox rating_amazon_cn" rel="v:rating" style="display:none"></div>
                <div class="rating_wrap clearbox rating_goodreads" style="display:none"></div>`);

                if (GM_getValue("enable_book_amazon.cn_rate", true)) {
                    rating_more_hit = true;
                    // 通过ISBN信息在亚马逊中国上搜索
                    getDoc("https://www.amazon.cn/s/?url=search-alias%3Dstripbooks&field-keywords=" + isbn, null, function (doc) {
                        let result_0 = $('div[data-index="0"]', doc);
                        if (result_0.length > 0) { // 这本书在亚马逊中国上能搜索到
                            let book_id_in_amazon = result_0.attr("data-asin");
                            let book_url = "https://www.amazon.cn/dp/" + book_id_in_amazon;
                            let vote_text = result_0.text().replace(/\n/g, " ");

                            // 这是一个很取巧的获取方式，很可能因为页面结构更改而失效。 最近检查于 2019.09.25
                            let _group = vote_text.match(/([\d.]+?) 颗星，最多 5 颗星 +([\d,]+)/);
                            if (_group) {
                                let _rating = _group[1];
                                let _vote = _group[2];

                                $('#interest_sectl div.rating_amazon_cn').html(starBlock("亚马逊中国", book_url, _rating, _vote, 5)).show();
                            }
                        } else {
                            $('#interest_sectl div.rating_amazon_cn').append(`<br>搜索亚马逊中国: <a target='_blank' href='${`https://www.amazon.cn/s?k=${encodeURI(title)}&i=stripbooks`}'>${title}</a>`);
                        }
                        $('#loading_more_rate').hide();
                    });
                }

                if (GM_getValue('enable_book_goodreads', false) && GM_getValue('apikey_goodreads', false)) {
                    rating_more_hit = true;
                    getJSON(`https://www.goodreads.com/book/review_counts.json?key=${GM_getValue('apikey_goodreads', '')}&format=json&isbns=${isbn}`, function (data) {
                        try {
                            let book = data['books'][0];

                            let goodread_id = book['id'];
                            let goodread_url = `https://www.goodreads.com/book/show/${goodread_id}`;
                            let rating = book['average_rating'];
                            let vote = book['work_ratings_count'];
                            $('#interest_sectl div.rating_goodreads').html(starBlock("GoodReads", goodread_url, rating, vote, 5)).show();
                        } catch (e) {
                            $('#interest_sectl div.rating_goodreads').append(`<br>搜索GoodReads: <a target='_blank' href='${`https://www.goodreads.com/search?q=${encodeURI(title)}`}'>${title}</a>`);
                        }
                        $('#loading_more_rate').hide();
                    });
                }

                if (!rating_more_hit) {
                    $('#loading_more_rate').hide();
                }
            }

            if (_version === "完整版") {
                site_map.push({
                    name: "会员精准匹配",
                    label: [
                        { name: "mLook©", link: "http://plugin.mlook.mobi/search?q=" + isbn, selector: "div.books div.fl.meta" },
                        { name: 'Gold©', link: 'http://goldroom.top/book/search/?q=' + isbn, selector: 'i.glyphicon-download-alt:not(:contains("0"))' },
                        { name: 'Z-Lib©', link: 'https://book4you.org/s/?e=1&q=' + isbn, selector: '#searchResultBox div.authors' },
                    ]
                });
                site_map.push({
                    name: "图书会员网站",
                    label: [
                        { name: '33文库', link: 'http://www.33file.com/search.php?word=' + title, selector: `table.td_line span.txtred:contains(${title})` },
                        { name: 'Bookle', link: `http://www.x5v.net/#search_${title}`, ajax: 'http://www.x5v.net/bsearch', data: `searchType=search&searchText=${title}`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, selector: 'a.book-link' },
                        { name: 'Goldroom', link: 'http://goldroom.top/book/search/?q=' + title, selector: 'i.glyphicon-download-alt:not(:contains("0"))' },
                        { name: 'IRead', link: 'http://www.iread.cf/?query=' + title, selector: 'li.book-item div.book-info' },
                        { name: "Kindle88", link: "http://www.kindle88.com/?s=" + title + writer, selector: "div.widget-content li.archive-thumb" },
                        { name: 'iamtxt', method: "post", link: 'https://www.iamtxt.com/e/search/index.php', data: `keyboard=${title}&show=title&tempid=2`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: 'div.sResult div.title' },
                        { name: "mLook", link: "http://plugin.mlook.mobi/search?q=" + title, selector: "div.books div.fl.meta" },
                        { name: 'rejoice', link: 'http://www.rejoiceblog.com/article/search/page/1/?keyword=' + title, selector: 'div.article a.title' },
                        { name: 'Z-Libary', link: 'https://book4you.org/s/?e=1&q=' + title, selector: '#searchResultBox div.authors' },
                        { name: 'Zure', link: 'https://zure.fun/book/search/?q=' + title, selector: 'div.item a' },
                        { name: "点书网", method: "post", link: "http://www.gezhongshu.com/search.php?mod=forum", data: `srchtxt=${title}${writer}&searchsubmit=yes`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: "div.tl li.pbw" },
                        { name: "慧眼看", link: "https://www.huiyankan.com/?s=" + title, selector: `h2.entry-title a:contains(${title})` },
                        { name: "精读", link: "https://www.jingdoo.net/?s=" + title, selector: `h3 a[title*='${title}']` },
                        { name: "慢慢游书", link: 'https://www.manmanyou.net/search.php?mod=forum&searchsubmit=yes&srchtxt=' + title, selector: "div.tl li.pbw", selector_need_login: "#messagelogin" },
                        { name: '偶书', link: 'https://obook.cc/index.php?app=search&ac=s&kw=' + title, selector: 'span.c9 + a' },
                        { name: "盘乐网书", link: 'https://www.panle.net/search.php?mod=forum&searchsubmit=yes&srchtxt=' + title, selector: "div.tl li.pbw" },
                        { name: "书点点", link: 'https://illumebook.com/?s=' + title, selector: 'a.ss_bt_a' },
                        { name: "书行万里", link: 'https://www.gpdf.net/?s=' + title, selector: `h2 a:contains(${title})` },
                        { name: "小书虫", link: 'https://www.wq1.net/?s=' + title, selector: `h3 a[title*='${title}']` },
                        { name: "星际图书", link: 'http://60.205.213.143:7743/find?q=' + title, selector: `h3.general_result_title a:contains(${title})` },
                        { name: "星空好书", link: 'https://www.goodepub.com/?s=' + title, selector: "h2.entry-title" },
                        { name: '雅书', method: "post", link: 'https://yabook.blog/e/search/index.php', data: `tbname=news&keyboard=${title}&show=title&tempid=1`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: 'div.main div.postinfo' },
                        { name: "掌上书苑", link: 'https://www.soepub.com/search/index/?q=' + title, selector: "div.book-info-title" },
                        { name: "知识库", link: 'https://book.zhishikoo.com/?s=' + title, selector: `h3 a[title*='${title}']` },
                    ]
                });
                site_map.push({
                    name: "图书公众号站",
                    label: [
                        { name: '519资源网', link: 'https://book.519.best/?key=' + title, selector: 'span.book-name a' },
                        { name: 'AiBooks', link: 'https://www.aibooks.cc/search/' + title, selector: `h3 > a[title*='${title}']` },
                        { name: 'Kindle吧', link: 'https://www.kindle8.cc/?s=' + title, selector: `h2 > a:contains(${title})` },
                        { name: 'NMOD', link: 'https://www.nmod.net/search/' + title, selector: `h3 > a[title*='${title}']` },
                        { name: 'SoBooks', link: 'https://sobooks.cc/search/' + title, selector: `h3 > a[title*='${title}'], h1.article-title a` },
                        { name: '爱书小站', link: 'https://www.aishuchao.com/?s=' + title, selector: `h2 a:contains(${title})` },
                        { name: '电子书基地', link: 'http://www.dzs.so/Book/List?Keyword=' + title, selector: `h5 a:contains(${title})` },
                        { name: '读书达人', link: 'http://www.dushudaren.com/?s=' + title, selector: `h2 a:contains(${title})` },
                        { name: '读书小站', link: 'https://ibooks.org.cn/?s=' + title, selector: `h3.entry-title a:contains(${title})` },
                        { name: '跪读网', link: 'https://orzbooks.com/search.php?q=' + title, selector: `h2 a:contains(${title})` },
                        { name: '琳宝书屋', link: 'https://linbaoshuwu.com/search/' + title + '/', selector: `h2 a:contains(${title})` },
                        { name: "皮皮书屋", link: 'http://www.pipibook.com/?s=' + title, selector: "div.list-content div.list-body" },
                        { name: '书单', link: 'https://ebooklist.mobi/?s=' + title, selector: `h2 > a:contains(${title})` },
                        { name: '天浪书屋', link: 'https://www.tianlangbooks.com/?s=' + title, selector: `h3 > a[title*='${title}']` },
                        { name: '图书库', link: 'http://www.tbookk.com/?s=' + title, selector: `h2 > a[title*='${title}']` },
                    ]
                });
            }
            site_map.push({
                name: "图书在线试读",
                label: [
                    { name: '多看阅读', link: `http://www.duokan.com/search/${title}`, selector: `div.wrap > a:contains(${title})` },
                    { name: '京东数字', link: `https://s-e.jd.com/Search?enc=utf-8&key=${title}${writer}`, selector: 'div.p-name a' },
                    { name: '亚马逊商店', link: 'https://www.amazon.cn/s?i=digital-text&k=' + isbn, selector: 'div.sg-col-inner h2' },
                ]
            });
            site_map.push({
                name: "图书精准匹配",
                label: [
                    { name: "EBH", link: "http://ebookhunter.ch/search/?keyword=" + isbn, selector: "#mains_left div.index_box_title.list_title" },
                    { name: "LibGen", link: "http://libgen.rs/search.php?column=title&req=" + isbn, selector: "table[rules='rows'] td[width='500']" },
                    { name: '科学文库', link: 'http://book.sciencereading.cn/shop/book/Booksimple/list.do?showQueryModel.nameIsbnAuthor=' + isbn, selector: 'div.book_detail_title b.kc_title' },
                    { name: '图书馆联盟', link: 'http://book.ucdrs.superlib.net/search?Field=all&channel=search&sw=' + isbn, selector: '#leftcommon + td table.book1' },
                ]
            });
            /** site_map.push({
                name: "图书网盘精准",
                label: [
                    { name: 'Downtr❏', link: 'https://downtr.cc/?do=search&subaction=search&story=' + isbn10, selector: '#dle-content div.title', selector_need_login: "h1 span:contains('Checking your browser')" },
                    { name: 'FilmSoft❏', link: 'http://filmsofts.com/?do=search&subaction=search&story=' + isbn10, selector: '#dle-content div.story', selector_need_login: "h1 span:contains('Checking your browser')" },
                    { name: 'Freshwap❏', link: 'http://www.freshwap.cc/?do=search&subaction=search&story=' + isbn10, selector: '#dle-content div.maincont', selector_need_login: "h1 span:contains('Checking your browser')" },
                    { name: 'OneDDL❏', link: 'https://oneddl.org/?do=search&subaction=search&story=' + isbn10, selector: '#dle-content div.con', selector_need_login: "h1 span:contains('Checking your browser')" },
                    { name: 'SoftArch❏', link: 'https://sanet.st/search/?category=any&filehosting=any&isbn=' + isbn10, selector: 'div.titles_list_box a.cellMainLink', selector_need_login: "h1 span:contains('Checking your browser')" },
                    { name: 'WarezSer❏', link: 'http://warez-serbia.com/index.php?do=search&subaction=search&story=' + isbn10, selector: '#dle-content div.post-info', selector_need_login: "h1 span:contains('Checking your browser')" },
                    { name: 'Win7DL❏', link: 'https://win7dl.org/?do=search&subaction=search&story=' + isbn10, selector: '#dle-content td.block_head_2', selector_need_login: "h1 span:contains('Checking your browser')" },
                ]
            }); **/
            site_map.push({
                name: "图书免费网站",
                label: [
                    { name: 'LoreFree', link: 'https://ebook2.lorefree.com/site/index?s=' + title, selector: 'div.body-content div.caption.book-content' },
                    { name: 'SaltTiger', link: 'https://salttiger.com/?s=' + title, selector: `h1.entry-title > a:contains(${title})` },
                    { name: '阿里盘搜书', link: 'https://www.alipanso.com/search.html?page=1&keyword=' + title, selector: 'h1.resource-title' },
                    { name: '爱悦读', link: 'https://www.iyd.wang/?s=' + title, selector: `h2.entry-title > a:contains(${title})` },
                    { name: '台大图书馆', link: 'http://ebooks.lib.ntu.edu.tw/Home/ListBooks?type=KeywordSearch&h_tag=&pageNumber=1&searchTopic=title&record_per_page=10&send=%E6%9F%A5%E8%A9%A2&keyword=' + title, selector: 'tbody td.content' },
                    { name: '中国哲学书', link: 'https://ctext.org/searchbooks.pl?if=gb&remap=gb&searchu=' + title, selector: 'ul.searchres div.ctext' },
                ]
            });
            if (has_ywm) {
                site_map.push({
                    name: "图书国外网站",
                    label: [
                        { name: 'BookFl', link: 'http://en.bookfi.net/s/?e=1&q=' + ywm, selector: `#searchResultBox h3.color1:Contains(${ywm})` },
                        { name: 'Booksee', link: 'http://en.booksee.org/s/?e=1&q=' + ywm, selector: `#searchResultBox h3.color1:Contains(${ywm})` },
                        { name: 'EPDF', link: 'https://epdf.tips/search/' + ywm, selector: `h3.note-title:Contains(${ywm})` },
                        { name: 'PDFDrive', link: 'https://www.pdfdrive.com/search?q=' + ywm, selector: `div.file-right a[href*='${stitle}']` },
                    ]
                });
            }
            site_map.push({
                name: "图书网盘搜索",
                label: [
                    { name: '阿里小站书', link: 'http://alixiaozhan.com/?q=' + title, ajax: "http://alixiaozhan.com/api/discussions?page%5Blimit%5D=3&include=mostRelevantPost&filter%5Bq%5D=" + title, type: "json", selector: 'data.length > 0' },
                    { name: '爱问资料', link: `http://ishare.iask.sina.com.cn/search/home.html?ft=all&cond=${ptitle}`, selector: 'ul.landing-txt-list h4.data-name' },
                    { name: '小白盘图书', link: 'http://www.xiaobaipan.com/list-' + title + '.html?order=size', selector: 'h4.job-title a' },
                    { name: '云盘小站书', link: 'https://aliyunshare.cn/?q=' + title, ajax: "https://aliyunshare.cn/api/discussions?page%5Blimit%5D=3&include=mostRelevantPost&filter%5Bq%5D=" + title, type: "json", selector: 'data.length > 0' },
                ]
            });
            site_map.push({
                name: "有声在线试听",
                label: [
                    { name: '懒人听书', link: 'http://www.lrts.me/search/book/' + title, selector: 'ul li.book-item' },
                    { name: '评书吧', link: 'http://www.pingshu8.com/search/1.asp?keyword=' + gtitle, selector: "table.TableLine div[align='left']" },
                    { name: '天方听书网', link: 'http://www.tingbook.com/Book/SearchResult.aspx?keyword=' + title, selector: 'ul.search_result_list h4.clearfix' },
                    { name: '听中国', link: 'http://www.tingchina.com/search1.asp?mainlei=0&lei=0&keyword=' + gtitle, selector: 'dl.singerlist1 li' },
                    { name: '喜马有声', link: 'https://www.ximalaya.com/search/' + title + '/', selector: `div.xm-album-cover__wrapper + a[title*='${title}']` },
                ]
            });
            site_map.push({
                name: "图书有声网站",
                label: [
                    { name: 'ABB', link: 'http://audiobookbay.nl/?s=' + title, selector: '#content div.postTitle' },
                ]
            });
        } else if (location.host === "music.douban.com") {
            // 页面元素定位
            let album_anchor = $('#info span.pl:contains("专辑类型")');  //专辑类型
            let medium_anchor = $('#info span.pl:contains("介质")');  //介质
            let album = album_anchor[0] ? fetch_anchor(album_anchor) : '';
            let is_single = album.match(/单曲/);
            let title = $('#wrapper > h1 > span')[0].textContent.split(' ').shift().replace(/[，]/g, " ").replace(/：.*$/, "");
            let gtitle = _encodeToGb2312(title, true);
            let ptitle = encodeURI(title).replace(/%/g, "%25");
            let singer = ' ' + $('#info > span > span.pl > a')[0].textContent;
            let gsinger = _encodeToGb2312(singer, true);
            if (_version === "完整版") {
                site_map.push({
                    name: "PT音乐顶配",
                    label: [
                        { name: "CHDBits♬", link: 'https://chdbits.co/torrents.php?cat406=1&cat408=1&incldead=1&search_area=1&notnewword=1&search=' + title + singer, },
                        { name: "CMCT♬", link: "https://hdcmct.org/torrents.php?cat508=1&incldead=1&search_area=1&notnewword=1&search=" + title + singer, },
                        { name: "HDChina♬", link: 'https://hdchina.org/torrents.php?cat408=1&incldead=1&search_area=1&notnewword=1&search=' + title + singer, selector: "table.torrent_list:last > tbody > tr:gt(0)" },
                        { name: "HDSky♬", link: 'https://hdsky.me/torrents.php?cat408=1&incldead=1&search_area=1&notnewword=1&search=' + title + singer, },
                        { name: "MTeam♬", link: 'https://kp.m-team.cc/torrents.php?cat408=1&cat434=1&incldead=1&search_area=1&notnewword=1&search=' + title + singer, },
                        { name: "OpenCD♬", link: 'https://open.cd/torrents.php?incldead=1&search_area=0&notnewword=1&search=' + title + singer, selector: "table.torrents:last > tbody > tr:gt(0)" },
                        { name: "OurBits♬", link: 'https://ourbits.club/torrents.php?cat=416&incldead=1&search_area=1&notnewword=1&search=' + title + singer, },
                        { name: "TTG♬", link: 'https://totheglory.im/browse.php?c=M&notnewword=1&search_field=分类%3A%60无损音乐FLAC%26APE%60+分类%3A%60%28电影原声%26Game%29OST%60 ' + title + singer, selector: "table#torrent_table:last > tbody > tr:gt(0)" },
                        { name: "U2♬", link: 'https://u2.dmhy.org/torrents.php?cat30=1&incldead=1&search_area=0&notnewword=1&search=' + title.split(' ')[0], },
                    ]
                });
                site_map.push({
                    name: "PT音乐标配",
                    label: [
                        { name: "HDCity♬", link: 'https://hdcity.city/pt?cat408=1&incldead=1&search_area=1&notnewword=1&iwannaseethis=' + title + singer, selector: "center > div > div > div.text" },
                        { name: "HDHome♬", link: 'https://hdhome.org/torrents.php?cat439=1&cat440=1&incldead=1&search_area=1&notnewword=1&search=' + title + singer, },
                        { name: "HDTime♬", link: 'https://hdtime.org/torrents.php?cat=408&incldead=1&search_area=1&notnewword=1&search=' + title + singer, },
                        { name: "JoyHD♬", link: 'https://www.joyhd.net/torrents.php?cat=414&incldead=1&search_area=1&notnewword=1&search=' + title + singer, },
                    ]
                });
                site_map.push({
                    name: "PT音乐教育",
                    label: [
                        { name: "NYPT♬", link: 'https://nanyangpt.com/torrents.php?cat407=1&incldead=1&search_area=1&notnewword=1&search=' + title + singer, selector: "table.torrents:last > tbody > tr" },
                        { name: "SJTU♬", link: 'https://pt.sjtu.edu.cn/torrents.php?cat420=1&cat421=1&cat422=1&cat423=1&cat425=1&cat426=1&incldead=1&search_area=1&notnewword=1&search=' + title + singer, selector: "table.torrents:last > tbody > tr" },
                    ]
                });
                site_map.push({
                    name: "PT音乐外站",
                    label: [
                        { name: "JPOP♬", link: 'https://jpopsuki.eu/torrents.php?searchstr=' + title + singer, selector: "#torrent_table > tbody > tr:gt(0)" },
                        { name: "Orpheus♬", link: 'https://orpheus.network/torrents.php?searchstr=' + title + singer, selector: "#torrent_table:last > tbody > tr.group_torrent:gt(0)" },
                        { name: "Red♬", link: 'https://redacted.ch/torrents.php?searchstr=' + title + singer, selector: "#torrent_table > tbody > tr.group_torrent:gt(0)" },
                        { name: "Waffles♬", link: 'https://waffles.ch/browse.php?q=' + title + singer, selector: "#browsetable:last > tbody > tr:gt(0)" },
                    ]
                });
                site_map.push({
                    name: "音乐论坛资源",
                    label: [
                        { name: "AIPT♬", link: 'http://pt.aipt123.org/table_list.php?search_area=1&notnewword=1&search=' + title + singer, },
                        { name: "磨坊", method: "post", link: "http://www.moofeel.com/search.php?mod=forum", data: `srchtxt=${gtitle}${gsinger}&searchsubmit=yes`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, rewrite_href: true, selector: "div.tl li.pbw" },
                        { name: "无损音乐网", link: 'https://www.so.com/s?q=site%3Awusunyinyue.cn+intitle:' + title + '%26%26' + singer.trim(), selector: 'ul.result li.res-list' },
                        { name: "盘乐网音", link: 'https://www.panle.net/search.php?mod=forum&searchsubmit=yes&srchtxt=' + title, selector: "div.tl li.pbw" },
                        { name: "炫音音乐", link: `http://so.musicool.cn/cse/search?s=10523158750213826925&q=${title}${singer}`, selector: "#results h3.c-title" },
                    ]
                });
            }
            site_map.push({
                name: "在线音乐播放",
                label: [
                    { name: 'QQ音乐', link: 'https://y.qq.com/portal/search.html#page=1&searchid=1&remoteplace=txt.yqq.top&t=album&w=' + title + singer, ajax: "https://c.y.qq.com/soso/fcgi-bin/client_search_cp?t=8&format=json&w=" + title + singer, type: "json", selector: 'data.album.totalnum > 0' },
                    { name: '百度音乐', link: 'http://music.baidu.com/search/album?key=' + title + singer, selector: '#album_list div.album-info' },
                    { name: '酷我音乐', link: 'http://sou.kuwo.cn/ws/NSearch?type=album&key=' + title + singer, selector: 'div.album p.musicName' },
                    { name: '咪咕音乐', link: `http://music.migu.cn/v2/search?type=album&keyword=${title}${singer}`, selector: `div.album-name font:contains(${title})` },
                    { name: '虾米音乐', link: `https://www.xiami.com/search/album/?key=${title}${singer}`, selector: `p.name > a[title='${title}'] + a[title='${singer.trim()}']` },
                    { name: '网易云音乐', link: 'https://music.163.com/#/search/m/?type=10&s=' + title + singer, ajax: "https://api.imjad.cn/cloudmusic/?type=search&s=" + title + singer, type: "json", selector: 'result.songCount > 0' },
                ]
            });
            if (is_single) {
                site_map.push({
                    name: "单曲无损网站",
                    label: [
                        { name: '51Ape', link: 'https://www.bing.com/search?q=site%3Awww.51ape.com+intitle%3A' + title + '+intitle%3A' + singer, selector: '#b_content div.b_caption' },
                    ]
                });
            }
            site_map.push({
                name: "音乐免费网站",
                label: [
                    { name: 'DTShot', link: 'http://www.dtshot.com/search/' + title + singer + '/', selector: `div.case_info div.meta-title:contains(${title})` },
                    { name: 'XZPC音乐', method: "post", link: 'http://www.xzpc6.com/#search_' + title, ajax: 'http://www.xzpc6.com/sou.php', data: `key=${title}`, headers: { "Content-Type": "application/x-www-form-urlencoded" }, selector: 'p a' },
                    { name: '爱无损', link: 'http://www.lovewusun.com/?s=' + title + singer, selector: '#main h2.entry-title' },
                    { name: '小浣熊音乐', link: `https://www.xiaohx.org/search?cat=5&key=${title}${singer}`, selector: `div.result_p a[title*='${title}']` },
                ]
            });
            site_map.push({
                name: "音乐国内网盘",
                label: [
                    { name: '小白盘音乐', link: 'http://www.xiaobaipan.com/list-' + title + '.html?order=size', selector: 'h4.job-title a' },
                ]
            });
            site_map.push({
                name: "音乐国外网盘",
                label: [
                    { name: 'AvaxHome♬', link: 'https://tavaz.xyz/search/?category_slug=music&query=' + title + singer, selector: 'div.col-xs-12.col-sm-8.col-md-8.col-lg-8 div.panel-heading' },
                    { name: 'Rutrack♬', link: 'http://rutracker.org/forum/search_cse.php?q=' + title, ajax: `https://www.google.com/search?q=allintitle:+${title}+site:rutracker.org`,selector: '`a > h3:contains(${title})`' },
                ]
            });
        }

        // 检查站点是否需要登陆的方法 res 应该是GM_xmlhttpRequests返回对象 ，返回bool值，true时为需要登陆
        function login_check(res) {
            let need_login = false;
            if (/login|verify|checkpoint|returnto/ig.test(res.finalUrl)) {
                need_login = true; // 检查最终的URL看是不是需要登陆
            } else if (/refresh: \d+; url=.+login.+/ig.test(res.responseHeaders)) {
                need_login = true; // 检查responseHeader有没有重定向
            } else {
                let responseText = res.responseText;
                if (typeof responseText === "undefined") {
                    need_login = true; // 检查最终的Text，如果什么都没有也可能说明需要登陆
                } else if (responseText.length < 800 && /login|not authorized/.test(responseText)) {
                    need_login = true; // 对Text进行检查，断言“过短，且中间出现login字段”即说明可能需要登陆
                }
            }
            return need_login;
        }

        function Exist_check(label) {
            let site = label.name;
            let psite = $(`a[data-name="${site}"]`);

            function HideTag() {
                if (GM_getValue('enable_adv_auto_hide',false)) {
                    $(psite).hide();
                }
            }

            function TagExist(link) {
                $(psite).css("background-color", GM_getValue("tag_bcolor_exist", "#e3f1ed"));
                $(psite).css("color", GM_getValue("tag_fcolor_exist", "#3377aa"));
                $(psite).attr("title", "资源存在");
                let storage_data = true;
                if (label.rewrite_href && label.rewrite_href === true) { // 重写链接
                    storage_data = cache.get(site, link || $(psite).attr("href"));
                    $(psite).attr("href", storage_data);
                }
                cache.add(site, storage_data);
            }

            function TagNotExist() {
                $(psite).css("background-color", GM_getValue("tag_bcolor_not_exist", "#f4eac2"));
                $(psite).css("color", GM_getValue("tag_fcolor_not_exist", "#3377aa"));
                $(psite).attr("title", "资源不存在");
                HideTag();
            }

            function TagNeedLogin() {
                $(psite).css("background-color", GM_getValue("tag_bcolor_need_login", ""));
                $(psite).css("color", GM_getValue("tag_fcolor_need_login", "#3377aa"));
                need_login_cache.add(site, true);
                $(psite).click(function () {
                    need_login_cache.del(site);
                });
                $(psite).attr("title", "站点需要登陆");
                HideTag();
            }

            function TagError(errtype) {
                $(psite).css("background-color", GM_getValue("tag_bcolor_error", ""));
                $(psite).css("color", GM_getValue("tag_fcolor_error", "#3377aa"));
                $(psite).attr("title", "遇到问题" + (errtype ? (" - " + errtype) : ""));
                HideTag();
            }

            // 这里假定有这个资源的就一直都有，直接使用第一次请求成功的时候缓存信息
            if (cache.get(site)) { TagExist(); return; }

            // 如果前次检查到这个站点需要登陆
            if (need_login_cache.get(site)) { TagNeedLogin(); return; }

            // 不然，则请求相关信息

            // 重写请求参数
            //if (typeof label.data === "object") {
            //    let myData = new FormData();
            //    for (let k in label.data) {
            //        myData.append(k,label.data.k);
            //    }
            //    label.data = myData;
            //}

            // 请求核心方法
            function check_core(label) {
                GM_xmlhttpRequest({
                    method: label.method || "GET",
                    url: label.ajax || label.link,
                    data: label.data,
                    headers: label.headers,
                    timeout: 45e3, // 默认45s服务器无响应算超时
                    onload: function (res) {
                        if (login_check(res)) {
                            TagNeedLogin();
                        } else {
                            try { // 开始解析返回信息
                                let responseText = res.responseText;
                                if (label.type && ["json", "jsonp"].includes(label.type)) { // 如果前面定义了返回类型是"json'或者"jsonp"
                                    if (label.type === "jsonp") {
                                        responseText = responseText.match(/[^(]+\((.+)\)/)[1];
                                    }
                                    let par = JSON.parse(responseText);
                                    if (eval("par." + label.selector)) {
                                        TagExist();
                                    } else {
                                        TagNotExist(); // 所有情况都失败则未存在
                                    }
                                } else { // 否则默认label.type的默认值为 html
                                    let doc = page_parser(res.responseText);
                                    let body = doc.querySelector("body");
                                    // 因为jQuery的选择器丰富，故这里不用 dom.querySelector() 而用 jQuery.find()
                                    if (label.selector_need_login && $(body).find(label.selector_need_login).length) {
                                        TagNeedLogin(); // 如果存在selector_need_login选择器，则先判断是否存在以确定是否需要登录
                                    } else if ($(body).find(label.selector || "table.torrents:last > tbody > tr:gt(0)").length) {
                                        TagExist(res.finalUrl); // 最后使用selector选择器判断资源是否存在
                                    } else {
                                        TagNotExist(); // 所有情况都失败则未存在
                                    }
                                }
                            } catch (e) {
                                TagError("解析错误");
                            }
                        }
                    },
                    onerror: function () { TagError("请求故障"); },
                    ontimeout: function () { TagError("请求超时"); },
                });
            }

            // 请求动作方法
            function check_func() {
                $(psite).attr("title", "正在请求信息中");
                if (label.csrf) { // 对某些启用了csrf的站点，先使用正常方式请求一次获取csrf值
                    GM_xmlhttpRequest({
                        method: "GET",
                        url: label.link,
                        timeout: 45e3, // 默认45s服务器无响应算超时
                        onload: function (res) {
                            if (!login_check(res)) {
                                try {
                                    let doc = page_parser(res.responseText);
                                    let csrf_ = $(`input[name='${label.csrf.name}'`, doc);
                                    let csrf_key = csrf_.attr("value"); // 获取csrf值
                                    label[label.csrf.update] += `&${label.csrf.name}=${csrf_key}`; // 更新对应选项
                                    check_core(label);
                                } catch (e) {
                                    TagError("解析故障");
                                }
                            }
                        },
                        onerror: function () { TagError("请求错误"); },
                        ontimeout: function () { TagError("请求超时"); },
                    });
                } else {
                    check_core(label);
                }
            }

            // 根据设置，是自动请求还是鼠标移动时在做请求
            if (GM_getValue("enable_adv_auto_search", true)) {
                check_func();
            } else {
                $(psite).mouseenter(function(e){ // 鼠标进入时才自动搜索并反馈
                    if ($(psite).attr('title') == 'empty') { // 防止重复请求
                        check_func();
                        $(psite).unbind('mouseenter');
                    }
                });
            }
        }

        function site_exist_status() {
            $("#drdm_req_status").show();
            for (let i = 0; i < site_map.length; i++) {
                let map_dic = site_map[i];
                if (GM_getValue(delete_site_prefix + map_dic.name, false)) {
                    continue;
                }
                $('#drdm_sites').append(`<div class="c-aside name-offline" data-id="${i}"><h2><i>${map_dic.name}</i>· · · · · ·</h2><div class=c-aside-body style="padding: 0 12px;"> <ul class=bs > </ul> </div> </div>`);

                let in_site_html = $(`div[data-id='${i}'] ul.bs`);
                for (let j = 0; j < map_dic.label.length; j++) {
                    let label = map_dic.label[j];
                    if (GM_getValue(delete_site_prefix + label.name, false)) {
                        continue;
                    }
                    in_site_html.append(`<a href="${label.link}" data-name="${label.name}" target="_blank" rel="nofollow" class="name-offline" title="empty">${label.name}</a>`);
                    Exist_check(label);

                }
            }

            update_status_interval = window.setInterval(update_req_status, 1e3);

            if (!GM_getValue("enable_adv_auto_search", true)) {
                $("#drdm_req_status_hide").click();
            }
        }
        site_exist_status();
    }

    // 脚本页面切换方法
    function wrapper_change(id, html, callback) {
        if ($(`div#wrapper > div#${id}`).length === 0) {
            $('div#wrapper').append(html);
            if (typeof callback === "function") {
                callback();
            }
        }
        let ele_inst = $(`div#wrapper > div#${id}`);
        let ele_other = $(`div#wrapper > div#content, div#footer`);
        if (ele_other.is(':visible')) {
            ele_other.hide(); ele_inst.show();
        } else {
            ele_other.show(); ele_inst.hide();
        }
    }

    // 加载豆列搜索
    if (GM_getValue("enable_doulist_search", true)) {
        GM_addStyle('#db-nav-movie a.movieannual {margin-left: 350px !important;}');
        $('div.nav-items ul').append('<li><a id="search_dlist" href="javascript:void(0);">豆列搜索</a></li>');
        $("#search_dlist").click(function () {
            let int_html = `<div id='drdm_doulist'><h1>豆列搜索</h1><div class="grid-16-8 clearfix"><div class="article"><div class="indent"><div class="movie-list"></div><a class="more" href="javascript:;" style="display:none">加载更多</a></div></div><div class="aside"><div><h2>豆列搜索 · · · · · ·</h2><div><span><p><div id="form-doulist"><input class="doulist" id="input-doulist" placeholder="Criterion, 46534919, ..." value=""</input><input type="submit" id="doulist-submit" value="search" /input></div></p></span><span style="" class="search_result c-aside-body"></span></div></div><div class="doulist_intro"><h2>豆列搜索说明 · · · · · ·</h2><p>输入你想搜的关键词，点击搜索。就这么简单。</p></div></div></div></div>`;
            wrapper_change("drdm_doulist", int_html, function () {
                let load_more = $("#drdm_doulist a.more");
                $('#doulist-submit').click(function () {
                    let doulist = $("#input-doulist").val();
                    $('div.movie-list').html("");
                    let get_doulist = function (doulist, page) {
                        load_more.text("加载中......").show();
                        getDoc('https://cn.bing.com/search?q=site%3awww.douban.com%2fdoulist+' + doulist + '&first=' + page, null, function (doc, res, meta) {
                            let result = $('ol#b_results .b_algo', doc);
                            result = result.filter(function () {
                                return $("a[href^='https://www.douban.com/doulist/']", this).length > 0;
                            });
                            if (result.length === 0) {
                                load_more.text('没有找到相关豆列');
                            }
                            else {
                                result.each(function () {
                                    let title = $(this).find("a[href^='https://www.douban.com/doulist/']");
                                    let caption = $(this).find("div.b_caption");

                                    let id = title.attr("href").match(/doulist\/(\d+)/)[1];
                                    let title_clean = title.text().replace(/(\(豆瓣\)|\s-\s豆瓣电影|\s-\s豆瓣)/, '').replace(/ - douban.com/, '');
                                    caption.find("div.b_attribution").remove();
                                    let detail = caption.html();

                                    if ($(`div.movie-list > div[data-dlist=${id}]`).length === 0) { // 重复的不再插入
                                        $('div.movie-list').append(`<div data-dlist="${id}"><div><h2 style="font-size:13px;"><a href="https://www.douban.com/doulist/${id}" target="_blank">${title_clean}</a></h2><div></div></div><div class="tags">${detail}<p class="ul"></p></div></div>`);
                                    }
                                });

                                // 更新加载信息
                                let load_id = page + 10;
                                load_more.text('加载更多');
                                load_more.one("click", function () {
                                    get_doulist(doulist, load_id);
                                });
                            }
                        });
                    }
                    get_doulist(doulist, 1);
                });
            });
        });
    }


    // 脚本设置
    $("#db-global-nav > div > div.top-nav-info").append(`<a href="javascript:;" id="drdm_setting_btn">脚本设置</a>`);
    $("#drdm_setting_btn").click(function () {
        let int_html = `<div id='drdm_setting'><h2>脚本设置界面正在开发中，请等待完善......</h2></div>`;
        wrapper_change("drdm_setting", int_html, function () {
            // TODO 评分信息，豆列搜索等杂项功能启用情况
            let config_setting = "<h1>脚本基本功能启用状况</h1><dl class='drdm-dl-horizontal'>";

            function config_setting_gen(name, key, note, def = true) {
                config_setting += `<dt>${name}</dt><dd><input type="checkbox" id="drdm_config_${key}" ${GM_getValue(key, def) ? 'checked' : ''} data-config="${key}"><label for="drdm_config_${key}"></label> ${note} </dd>`;
            }

            config_setting_gen("额外样式", "enable_extra_stylesheet", "注入一些额外的CSS样式屏蔽豆瓣广告等", true);
            config_setting_gen("豆列搜索", "enable_doulist_search", "对豆列进行搜索（通过\`cn.bing.com\`搜索）");
            config_setting_gen("电影简介生成", "enable_mediainfo_gen", "生成符合PT站点电影简介信息（Mediainfogen格式）", false);
            config_setting_gen("各类排行榜", "enable_top_rang_tag", `显示来自 <a href="https://github.com/bimzcy/rank4douban">bimzcy/rank4douban</a> 的各种排行榜`);
            config_setting_gen("启用全站自动搜索", "enable_adv_auto_search", "启用可让脚本自动搜索全部站点（会消耗CPU及网络资源），不启用则仅当鼠标移至对应站点时搜索");
            config_setting_gen("自动隐藏搜索失败站点","enable_adv_auto_hide","搜索时自动隐藏搜索失败（资源不存在,需要登陆,遇到问题）站点，默认关闭", false);
            config_setting_gen("搜索完成后隐藏提示条","enalbe_adv_auto_tip_hide","搜索结束后自动隐藏搜索情况提示条，默认关闭且不建议开启", false);
            config_setting_gen("展示IMDB增强信息", "enable_imdb_ext_info", "展示制片成本、本国首周票房、北美首周票房、总票房等来自IMDb的影片增强信息");
            config_setting_gen("烂番茄评分", "enable_tomato_rate", "展示烂番茄评分信息");
            config_setting_gen("动漫评分", "enable_anime_rate", "展示动漫影视的AniDB、Bgm、Mal等评分");
            config_setting_gen("蓝光发售日", "enable_blue_date", "展示蓝光的发售日期(来自IMDb)");
            config_setting_gen("亚马逊图书评分", "enable_book_amazon.cn_rate", `展示在<a href="https://www.amazon.cn/" target="_blank">亚马逊中国</a> 上有对应ISBN信息的图书评分信息`);
            config_setting_gen("GoodReads图书评分","enable_book_goodreads",`展示在 <a href="https://www.goodreads.com" target="_blank">GoodReads</a> 上有对应ISBN信息的图书评分信息，设置你的APIKEY: <input id='drdm_setting_apikey_goodreads' type='text' value='${GM_getValue('apikey_goodreads','')}'></input> (<a href='//blog.rhilip.info/archives/1124/' target='_blank'>说明</a>)`,false);

            config_setting += `</dl><br>`;

            // 构造站点启用信息
            let setting_site = "<h1>搜索站点启用情况(在当前页面条件下)</h1>";
            for (let i = 0; i < site_map.length; i++) {
                let map_dic = site_map[i];
                setting_site += `<div><h2>${map_dic.name} <input type="checkbox" id="${'drdm_config_site_' + map_dic.name}" ${GM_getValue(delete_site_prefix + map_dic.name, false) ? '' : 'checked'} data-config="${delete_site_prefix + map_dic.name}" data-par="${map_dic.name}" data-type="map"><label for="${'drdm_config_site_' + map_dic.name}"></label></h2><table><tbody><tr>`;
                for (let j = 0; j < map_dic.label.length; j++) {
                    let label = map_dic.label[j];
                    setting_site += `<td style="text-align:right;"><span>${label.name}</span><input type="checkbox" id="${'drdm_config_site_' + label.name}" ${GM_getValue(delete_site_prefix + map_dic.name, false) || GM_getValue(delete_site_prefix + label.name, false) ? '' : 'checked'} ${GM_getValue(delete_site_prefix + map_dic.name, false) ? 'disabled' : ''} data-config="${delete_site_prefix + label.name}" data-par="${map_dic.name}" data-type="site"><label for="${'drdm_config_site_' + label.name}"></label></td>`;
                    if ((j + 1) % 7 === 0) {
                        setting_site += '</tr><tr>';
                    }
                }
                setting_site += "</tbody></table></div><hr>";
            }
            $("#drdm_setting").append(config_setting + setting_site);
            $("input[id^='drdm_config_']").click(function () {
                let that = $(this);
                GM_setValue(that.attr("data-config"), that.attr("data-config").match(delete_site_prefix) ? !that.prop("checked") : that.prop("checked"));
                if (that.attr("data-type") && that.attr("data-type") === "map") {
                    let par = that.attr("data-par");
                    $(`input[id^='drdm_config_site_'][data-type='site'][data-par='${par}']`).prop("disabled", !that.prop("checked")).prop("checked", that.prop("checked"));
                }
            });

            // 其他回调
            $('input#drdm_setting_apikey_goodreads').on('input change',function () {
                let that = $(this);
                GM_setValue('apikey_goodreads', that.val());
            });
        });
    });
});
