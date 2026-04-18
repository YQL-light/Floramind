Page({
  data: {
    myPlants: [],
    hotPlants: [],
    loading: true
  },

  onLoad() {
    this.fetchMyPlants();
    this.fetchHotPlants();
  },

  onShow() {
    // 每次显示页面时刷新
    this.fetchMyPlants();
  },

  // 获取我的植物列表
  fetchMyPlants() {
    const token = wx.getStorageSync('token');
    const app = getApp();
    
    this.setData({ loading: true });
    
    wx.request({
      url: app.globalData.baseUrl + '/get_plants',
      method: 'GET',
      header: {
        'Authorization': 'Bearer ' + token
      },
      success: (res) => {
        console.log('后端返回:', res.data);
        
        if (res.data.code === 200) {
          let plants = [];
          
          // 处理数据格式
          if (Array.isArray(res.data.data)) {
            plants = res.data.data;
          }
          
          // 转换为页面需要的格式
          const myPlants = plants.map(plant => {
            // 计算距离上次浇水的天数
            let days = 0;
            if (plant.last_watered) {
              const lastWatered = new Date(plant.last_watered);
              const today = new Date();
              const diffTime = Math.abs(today - lastWatered);
              days = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            }
            
            return {
              id: plant.id,
              name: plant.nickname || plant.species || '未知植物',  // 优先用昵称
              days: days,
              image: plant.plantAvatar_url || '/images/plant-placeholder.png'
            };
          });
          
          this.setData({ myPlants });
        }
      },
      fail: (err) => {
        console.error('获取植物失败:', err);
      },
      complete: () => {
        this.setData({ loading: false });
      }
    });
  },

  // 获取热门植物推荐（暂时保留静态数据，后续可替换）
  fetchHotPlants() {
    // 可以调用后端推荐接口，或者保留静态数据
    // 暂时保留原来的静态数据
    this.setData({
      hotPlants: [
        {
          id: 11,
          name: "多肉",
          image: "https://images.unsplash.com/photo-1459156212016-c812468e2115?auto=format&fit=crop&w=600&q=80"
        },
        {
          id: 12,
          name: "绿萝",
          image: "https://images.unsplash.com/photo-1463320726281-696a485928c7?auto=format&fit=crop&w=600&q=80"
        },
        {
          id: 13,
          name: "仙人掌",
          image: "https://images.unsplash.com/photo-1453906971074-ce568cccbc63?auto=format&fit=crop&w=600&q=80"
        },
        {
          id: 14,
          name: "月季",
          image: "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?auto=format&fit=crop&w=600&q=80"
        }
      ]
    });
  },

  // 返回花园
  onBackToGarden() {
    wx.switchTab({ url: "/pages/dashboard/dashboard" });
  },

  // 添加植物
  onAddPlant() {
    wx.navigateTo({ url: "/pages/reminders/reminders" });
  },

  // 点击植物查看日记
  onPlantTap(e) {
    const plantId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/diary/index?plantId=${plantId}`
    });
  }
});