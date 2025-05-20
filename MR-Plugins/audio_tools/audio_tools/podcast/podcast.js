const app = Vue.createApp({
  data() {
    return {
      status: true,
      isMobile: true,
      isLoading: true,
      windowWidth: window.innerWidth,
      podcasts: {},
      podcastNum: 0,
      searchTerm: "",
      currentPage: 1,
      pageSize: 32, // 每页显示的数量
      visiblePodcasts: {}, // 可见的播客数据
      searching: false,
      contextMenuVisible: false,
      contextMenuX: 0,
      contextMenuY: 0,
      selectedUrl: "",
      podcast_title: "",
      cover_url: "",
      podcast_author: "",
      podcast_reader: "",
      sync_time: "",
      update_time: "",
      isApple: false,
    };
  },
  computed: {
    isMobileDevice() {
      const mobileRegex = /Mobi|Android|iPhone|iPad|iPod/i;
      return mobileRegex.test(navigator.userAgent);
    },
    gridSettings() {
      if (this.windowWidth <= 450) {
        return { columnNum: 2, gutter: 10 };
      } else if (this.windowWidth < 600) {
        return { columnNum: 3, gutter: 15 };
      } else if (this.windowWidth < 800) {
        return { columnNum: 4, gutter: 18 };
      } else if (this.windowWidth < 1000) {
        return { columnNum: 5, gutter: 20 };
      } else if (this.windowWidth < 1200) {
        return { columnNum: 5, gutter: 23 };
      } else if (this.windowWidth < 1450) {
        return { columnNum: 6, gutter: 28 };
      } else if (this.windowWidth < 1700) {
        return { columnNum: 7, gutter: 25 };
      } else {
        return { columnNum: 8, gutter: 32 };
      }
    },
    pagedPodcasts() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return Object.entries(this.podcasts)
        .slice(start, end)
        .reduce((obj, [title, podcast]) => ({ ...obj, [title]: podcast }), {});
    },
  },
  methods: {
    playHoverSound() {
      if (this.audioElement) {
        this.audioElement.pause();
        this.audioElement = null;
      }
      const audioContext = new (window.AudioContext ||
        window.webkitAudioContext)();
      this.audioElement = new Audio("/static/podcast/tock.mp3");
      const source = audioContext.createMediaElementSource(this.audioElement);
      source.connect(audioContext.destination);
      this.audioElement.play();
    },
    ToXmly(url) {
      window.open(url, "_blank");
    },
    setDefaultImage(event) {
      event.target.src = "/static/podcast/default.jpg";
    },
    getRelativeCoverUrl(coverUrl) {
      const startIndex = coverUrl.indexOf("/static/podcast/");
      if (startIndex !== -1) {
        return coverUrl.substring(startIndex);
      }
      return null;
    },
    // 跳转
    showContextMenu(
      event,
      url,
      title,
      cover_url,
      author,
      reader,
      sync_time,
      update_time
    ) {
      // 检测设备类型
      var isAppleDevice = /(iPhone|iPad|iPod|Mac)/i.test(navigator.userAgent);
      this.isApple = isAppleDevice;
      event.preventDefault();
      this.selectedUrl = url;
      this.podcast_title = title;
      this.cover_url = cover_url;
      this.podcast_author = author;
      this.podcast_reader = reader;
      // 加入判定，如果 sync_time 和 update_time 未定义，则赋值为空字符串
      if (typeof sync_time === "undefined") {
        this.sync_time = "";
      } else {
        this.sync_time = sync_time;
      }

      if (typeof update_time === "undefined") {
        this.update_time = "";
      } else {
        this.update_time = update_time;
      }
      // console.log(this.podcast_author)
      this.contextMenuX = event.pageX;
      this.contextMenuY = event.pageY;
      // this.contextMenuX = event.offsetX;
      // this.contextMenuY = event.offsetY;
      // 根据屏幕宽度判断弹窗什么时候向左移动，防止在最后一个播客源点击右键无法显示完整弹窗或被内容布局变形
      if (this.windowWidth <= 400) {
        // if (this.contextMenuX > this.windowWidth * 0.5) {
        //     this.contextMenuX -= 226;
        // };
        if (this.windowWidth <= 400) {
          if (this.contextMenuX >= this.windowWidth * 0.65) {
            this.contextMenuX -= 226;
          } else if (
            this.contextMenuX >= this.windowWidth * 0.5 &&
            this.contextMenuX < this.windowWidth * 0.65
          ) {
            this.contextMenuX -= 180;
          } else if (
            this.contextMenuX >= this.windowWidth * 0.4 &&
            this.contextMenuX < this.windowWidth * 0.5
          ) {
            this.contextMenuX -= 100;
          } else if (
            this.contextMenuX >= this.windowWidth * 0.3 &&
            this.contextMenuX < this.windowWidth * 0.4
          ) {
            this.contextMenuX -= 50;
          }
        }
      } else if (this.windowWidth < 600) {
        if (this.contextMenuX > this.windowWidth * 0.65) {
          this.contextMenuX -= 226;
        } else if (
          this.contextMenuX >= this.windowWidth * 0.5 &&
          this.contextMenuX < this.windowWidth * 0.65
        ) {
          this.contextMenuX -= 180;
        } else if (
          this.contextMenuX >= this.windowWidth * 0.4 &&
          this.contextMenuX < this.windowWidth * 0.5
        ) {
          this.contextMenuX -= 100;
        } else if (
          this.contextMenuX >= this.windowWidth * 0.3 &&
          this.contextMenuX < this.windowWidth * 0.4
        ) {
          this.contextMenuX -= 50;
        }
      } else if (this.windowWidth < 800) {
        if (this.contextMenuX > this.windowWidth * 0.57) {
          this.contextMenuX -= 220;
        }
      } else if (this.windowWidth < 1000) {
        if (this.contextMenuX > this.windowWidth * 0.7) {
          this.contextMenuX -= 220;
        }
      } else if (this.windowWidth < 1200) {
        if (this.contextMenuX > this.windowWidth * 0.72) {
          this.contextMenuX -= 220;
        }
      } else if (this.windowWidth < 1450) {
        if (this.contextMenuX > this.windowWidth * 0.76) {
          this.contextMenuX -= 210;
        }
      } else if (this.windowWidth < 1700) {
        if (this.contextMenuX > this.windowWidth * 0.83) {
          this.contextMenuX -= 215;
        }
      } else {
        if (this.contextMenuX > this.windowWidth * 0.87) {
          this.contextMenuX -= 210;
        }
      }
      this.contextMenuVisible = true;
    },
    PhoneContextMenu(
      event,
      url,
      title,
      cover_url,
      author,
      reader,
      sync_time,
      update_time
    ) {
      event.stopPropagation(); // 防止事件冒泡
      if (this.isMobile) {
        this.showContextMenu(
          event,
          url,
          title,
          cover_url,
          author,
          reader,
          sync_time,
          update_time
        );
        this.contextMenuY -= 180;
      }
    },
    hideContextMenuOnClick(event) {
      // 点击任意位置隐藏上下文弹出菜单
      this.contextMenuVisible = false;
    },
    copyUrl() {
      const textarea = document.createElement("textarea");
      textarea.value = this.selectedUrl;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      this.contextMenuVisible = false;
    },
    openUrl() {
      window.open(this.selectedUrl, "_blank");
      this.contextMenuVisible = false;
    },
    ToPodcast(url) {
      // 检测设备类型
      var isAppleDevice = /(iPhone|iPad|iPod|Mac)/i.test(navigator.userAgent);
      this.isApple = isAppleDevice;
      if (isAppleDevice) {
        // 如果是苹果设备，使用 'podcast:' + url 打开链接
        // window.location.href = url;
        // window.open('podcast:' + url, '_blank');
        location.href = "podcast:" + url;
      } else {
        // 如果不是苹果设备，在新标签页打开链接
        window.open(url, "_blank");
      }
    },
    fetchPodcasts() {
      axios({
        method: "get",
        url: "/static/podcast/audio/podcast.json?" + new Date().getTime(),
      })
        .then((res) => {
          if (
            typeof res.data === "object" &&
            Object.keys(res.data).length > 0
          ) {
            // 扁平化数据结构
            const flattenedData = {};
            for (let [title, authorData] of Object.entries(res.data)) {
              for (let [author, readerData] of Object.entries(authorData)) {
                for (let [reader, podcast] of Object.entries(readerData)) {
                  const uniqueKey = title + "_" + author + "_" + reader; // 仅用于确保键的唯一性
                  flattenedData[uniqueKey] = {
                    title: title, // 书名
                    podcast_author: author, // 作者
                    reader: reader, // 演播者
                    ...podcast,
                  };
                }
              }
            }
            this.podcasts = flattenedData;
            this.podcastNum = Object.keys(flattenedData).length;
            this.status = true;
            this.loadInitialPodcasts(); // 初始化可见数据
          } else {
            this.status = false;
          }
          this.isLoading = false;
        })
        .catch((e) => {
          this.status = false;
        });
    },
    // 搜索书名，作者，演播者
    filteredPodcasts() {
      const term = this.searchTerm.trim().toLowerCase();
      if (!term) {
        return this.podcasts;
      }
      return Object.entries(this.podcasts)
        .filter(([title, podcast]) => {
          return (
            title.toLowerCase().includes(term) ||
            (podcast.reader && podcast.reader.toLowerCase().includes(term)) ||
            (podcast.podcast_author &&
              podcast.podcast_author.toLowerCase().includes(term))
          );
        })
        .reduce((obj, [title, podcast]) => ({ ...obj, [title]: podcast }), {});
    },
    filterPodcasts(term) {
      this.searching = true;
      term = term.trim().toLowerCase();
      if (!term) {
        this.visiblePodcasts = this.podcasts;
        return;
      }
      this.visiblePodcasts = Object.fromEntries(
        Object.entries(this.podcasts).filter(([title, podcast]) => {
          return (
            title.toLowerCase().includes(term) ||
            (podcast.reader && podcast.reader.toLowerCase().includes(term)) ||
            (podcast.podcast_author &&
              podcast.podcast_author.toLowerCase().includes(term))
          );
        })
      );
      console.log("Matched titles:", Object.keys(this.visiblePodcasts));
    },
    performSearch() {
      // 重置 currentPage 和 searching 标志
      this.currentPage = 1;
      this.searching = this.searchTerm.trim().length > 0;

      if (this.searching) {
        console.log("搜索关键词:", this.searchTerm);
        this.filterPodcasts(this.searchTerm);
      } else {
        // 如果搜索词为空，则重置为原始的可见播客列表
        console.log("搜索关键词为空，不搜索");
        this.loadInitialPodcasts();
      }
    },
    // 判断是否在iframe中
    isInIframe() {
      try {
        return window.self !== window.top;
      } catch (e) {
        return true;
      }
    },
    handleResize() {
      this.windowWidth = window.innerWidth;
    },
    // 判断是否在主屏幕中
    isAddedToHomeScreen() {
      return (
        window.navigator.standalone ||
        window.matchMedia("(display-mode: standalone)").matches
      );
    },
    getPodcastUrl(url) {
      if (url) {
        const newurl = url.origin + "/static/podcast/index.html";
        console.log("新网页:", newurl);
        return newurl;
      }
      return "";
    },
    adjustBgDivHeight() {
      const bgDiv = document.getElementById("bg-div");
      const searchBg = document.getElementById("search-bg");
      window.addEventListener("scroll", () => {
        const scrollPosition = window.scrollY || window.pageYOffset;
        const fixedPosition = 165; // 在哪个位置开始固定
        if (scrollPosition >= fixedPosition) {
          searchBg.style.boxShadow = "0 8px 18px rgba(0, 0, 0, 0.5)"; // 在滚动到固定位置后设置为30px
          searchBg.style.borderBottom = "1px solid rgba(255, 255, 255, 0.1)";
        } else {
          searchBg.style.boxShadow = "0 8px 18px rgba(0, 0, 0, 0)"; // 在滚动到固定位置后设置为30px
          searchBg.style.borderBottom = "1px solid rgba(255, 255, 255, 0)";
        }
      });
      // const bgUrl = this.getBg(this.isSmallScreen);
      if (this.isAddedToHomeScreen() && !this.isInIframe()) {
        const originalHeight = parseInt(bgDiv.style.height);
        const updatedHeight = originalHeight + 50;
        bgDiv.style.height = updatedHeight + "px";
        searchBg.style.paddingTop = "0px";
        const initialOffsetTop = searchBg.offsetTop;
        window.addEventListener("scroll", () => {
          const scrollPosition = window.scrollY || window.pageYOffset;
          const fixedPosition = 165; // 在哪个位置开始固定
          if (scrollPosition >= fixedPosition) {
            searchBg.style.paddingTop = "50px"; // 在滚动到固定位置后设置为30px
            searchBg.style.boxShadow = "0 8px 18px rgba(0, 0, 0, 0.5)"; // 在滚动到固定位置后设置为30px
            searchBg.style.borderBottom = "1px solid rgba(255, 255, 255, 0.1)";
          } else {
            searchBg.style.paddingTop = "0px"; // 在滚动位置低于固定位置时设置回0
            searchBg.style.boxShadow = "0 8px 18px rgba(0, 0, 0, 0)"; // 在滚动到固定位置后设置为30px
            searchBg.style.borderBottom = "1px solid rgba(255, 255, 255, 0)";
          }
        });
      }
      // if (this.isSmallScreen) {
      if (this.isMobile) {
        document.getElementById("bg-img").style.filter = "blur(0)";
      } else {
        document.getElementById("bg-img").src = "/static/podcast/bg_pc.png";
        document.getElementById("bg-img").style.filter = "blur(5px)";
      }
    },
    handleScroll(event) {
      console.log("handleScroll");
      const app = event.target.documentElement;
      const scrollBottom = app.scrollHeight - app.scrollTop - app.clientHeight;
      if (scrollBottom < 100) {
        this.loadMorePodcasts();
      }
    },
    loadInitialPodcasts() {
      const newPodcasts = this.pagedPodcasts;
      this.visiblePodcasts = newPodcasts;
    },
    loadMorePodcasts() {
      if (this.searching) return; // 如果正在搜索，就不加载更多的播客项
      this.currentPage++;
      const newPodcasts = this.pagedPodcasts;
      this.visiblePodcasts = { ...this.visiblePodcasts, ...newPodcasts };
    },
  },
  watch: {
    windowWidth(newWidth) {
      this.adjustBgDivHeight();
      this.handleResize();
    },
  },
  mounted() {
    // 添加全局点击事件监听器，点击任何地方都隐藏上下文菜单
    document.addEventListener("click", this.hideContextMenuOnClick);
    this.fetchPodcasts();
    this.isMobile = this.isMobileDevice;
    window.addEventListener("resize", this.handleResize);
    window.addEventListener("orientationchange", this.handleResize);
    this.adjustBgDivHeight();
    // console.log(this.isMobile)
    window.addEventListener("scroll", this.handleScroll, true);
  },
  beforeUnmount() {
    // 在组件销毁前移除全局点击事件监听器
    document.removeEventListener("click", this.hideContextMenuOnClick);
    window.removeEventListener("resize", this.handleResize);
    window.removeEventListener("orientationchange", this.handleResize);
    window.removeEventListener("scroll", this.handleScroll, true);
  },
});
app.use(vant);
app.use(vant.Lazyload);
app.mount("#app");
