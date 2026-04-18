// pages/diary/index.js

/**
 * API 接口 - 接入真实后端
 */
const app = getApp();

const PlantAPI = {
  /**
   * 获取植物列表和日记
   * @returns {Promise<Array>} 植物数据数组
   */
  async getPlants() {
    const token = wx.getStorageSync('token');
    
    return new Promise((resolve, reject) => {
      // 1. 获取植物列表
      wx.request({
        url: app.globalData.baseUrl + '/get_plants',
        method: 'GET',
        header: { 'Authorization': 'Bearer ' + token },
        success: (plantRes) => {
          if (plantRes.data.code === 200) {
            let plants = [];
            if (Array.isArray(plantRes.data.data)) {
              plants = plantRes.data.data;
            }
            
            // 2. 获取日记列表
            wx.request({
              url: app.globalData.baseUrl + '/diary/diaries',
              method: 'GET',
              header: { 'Authorization': 'Bearer ' + token },
              success: (diaryRes) => {
                const diaries = diaryRes.data.data?.diaries || [];
                
                // 3. 合并数据
                const formattedPlants = plants.map(plant => {
                  // 计算天数
                  let days = 0;
                  if (plant.last_watered) {
                    const lastWatered = new Date(plant.last_watered);
                    const today = new Date();
                    const diffTime = Math.abs(today - lastWatered);
                    days = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                  }
                  
                  // 获取该植物的日记
                  const plantDiaries = diaries
                    .filter(d => d.plantId == plant.id)
                    .map(d => ({
                      id: d.id,
                      date: d.date?.split('T')[0] || d.date || '',
                      actions: [d.activityType].filter(a => a),
                      note: d.content || '',
                      images: d.photos || [],
                      swipeX: 0
                    }));
                  
                  return {
                    id: String(plant.id),
                    name: plant.nickname || plant.species || '未知植物',
                    avatar: plant.plantAvatar_url || '/images/plant-placeholder.svg',
                    addedDate: plant.created_at?.split('T')[0] || '2025年1月1日',
                    daysUntilWater: days,
                    diaryEntries: plantDiaries
                  };
                });
                
                resolve(formattedPlants);
              },
              fail: reject
            });
          } else {
            reject(plantRes.data);
          }
        },
        fail: reject
      });
    });
  },

  /**
   * 获取天气信息
   */
  async getWeather() {
    const token = wx.getStorageSync('token');
    
    return new Promise((resolve, reject) => {
      wx.request({
        url: app.globalData.baseUrl + '/diary/weather/current',
        method: 'GET',
        header: { 'Authorization': 'Bearer ' + token },
        success: (res) => {
          if (res.data.code === 200) {
            const temp = parseInt(res.data.data.temp) || 20;
            resolve({
              condition: res.data.data.text || '晴',
              tempLow: temp - 3,
              tempHigh: temp + 3,
              icon: res.data.data.icon || 'sunny'
            });
          } else {
            reject(res.data);
          }
        },
        fail: reject
      });
    });
  },

  /**
   * 添加日记条目
   */
  async addDiaryEntry(plantId, entry) {
    const token = wx.getStorageSync('token');
    
    return new Promise((resolve, reject) => {
      wx.request({
        url: app.globalData.baseUrl + '/diary/diaries',
        method: 'POST',
        header: {
          'Authorization': 'Bearer ' + token,
          'Content-Type': 'application/json'
        },
        data: {
          plantId: plantId,
          title: entry.note?.substring(0, 20) || '日记',
          content: entry.note || '',
          activityType: entry.actions[0] || '',
          photos: entry.images,
          date: new Date().toISOString().split('T')[0]
        },
        success: (res) => {
          if (res.data.code === 200) {
            resolve({
              id: res.data.data?.diaryId || 'e' + Date.now(),
              date: new Date().toLocaleDateString('zh-CN'),
              actions: entry.actions,
              note: entry.note,
              images: entry.images,
              swipeX: 0
            });
          } else {
            reject(res.data);
          }
        },
        fail: reject
      });
    });
  },

  /**
   * 删除日记条目
   */
  async deleteDiaryEntry(plantId, entryId) {
    const token = wx.getStorageSync('token');
    
    return new Promise((resolve, reject) => {
      wx.request({
        url: app.globalData.baseUrl + `/diary/diaries/${entryId}`,
        method: 'DELETE',
        header: { 'Authorization': 'Bearer ' + token },
        success: (res) => {
          if (res.data.code === 200) {
            resolve(true);
          } else {
            reject(res.data);
          }
        },
        fail: reject
      });
    });
  },

  /**
   * 上传图片（返回本地路径，提交时使用）
   */
  async uploadImage(filePath) {
    // 暂时返回本地路径，后续可替换为真实上传
    return filePath;
  }
};

Page({
  data: {
    
    weather: {
      condition: '晴',
      tempLow: 6,
      tempHigh: 15
    },
    plants: [],
    currentPlantIndex: 0,
    currentPlant: null,
    activeTab: 'plant',
    showAddModal: false,
    // 新增：添加日记时选中的植物索引
    selectedPlantIndex: 0,
    newEntry: {
      note: '',
      actions: [],
      images: []
    },
    touchStartX: 0,
    touchStartY: 0,
    currentSwipeId: null
  },

  onLoad: function (options) {
    this.loadData();
  },

  async loadData() {
    try {
      wx.showLoading({ title: '加载中...' });
      
      const [plants, weather] = await Promise.all([
        PlantAPI.getPlants(),
        PlantAPI.getWeather()
      ]);
      
      this.setData({
        plants: plants,
        weather: weather,
        currentPlant: plants[0] || null
      });
      
      wx.hideLoading();
    } catch (error) {
      wx.hideLoading();
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
      console.error('加载数据失败:', error);
    }
  },

  onPullDownRefresh: function () {
    this.loadData().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  onPlantSwiperChange: function (e) {
    const index = e.detail.current;
    this.setData({
      currentPlantIndex: index,
      currentPlant: this.data.plants[index]
    });
  },

  switchTab: function (e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
  },

  /**
   * 新增：选择植物（添加日记时）
   */
  onPlantSelect: function (e) {
    this.setData({
      selectedPlantIndex: parseInt(e.detail.value)
    });
  },

  openAddModal: function () {
    this.setData({
      showAddModal: true,
      // 默认选中当前浏览的植物
      selectedPlantIndex: this.data.currentPlantIndex,
      newEntry: {
        note: '',
        actions: [],
        images: []
      }
    });
  },

  closeAddModal: function () {
    this.setData({ showAddModal: false });
  },

  onNoteInput: function (e) {
    this.setData({
      'newEntry.note': e.detail.value
    });
  },

  toggleAction: function (e) {
    const action = e.currentTarget.dataset.action;
    const actions = [...this.data.newEntry.actions];
    const index = actions.indexOf(action);
    
    if (index > -1) {
      actions.splice(index, 1);
    } else {
      actions.push(action);
    }
    
    this.setData({
      'newEntry.actions': actions
    });
  },

  chooseImage: function () {
    const that = this;
    const remainCount = 9 - this.data.newEntry.images.length;
    
    wx.chooseMedia({
      count: remainCount,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: async function (res) {
        wx.showLoading({ title: '处理中...' });
        
        try {
          const imagePaths = res.tempFiles.map(file => file.tempFilePath);
          that.setData({
            'newEntry.images': [...that.data.newEntry.images, ...imagePaths]
          });
          wx.hideLoading();
        } catch (error) {
          wx.hideLoading();
          wx.showToast({
            title: '处理失败',
            icon: 'none'
          });
        }
      }
    });
  },

  removeImage: function (e) {
    const index = e.currentTarget.dataset.index;
    const images = [...this.data.newEntry.images];
    images.splice(index, 1);
    
    this.setData({
      'newEntry.images': images
    });
  },

  submitEntry: async function () {
    // 修改：使用 selectedPlantIndex 获取目标植物
    const { newEntry, selectedPlantIndex, plants } = this.data;
    const targetPlant = plants[selectedPlantIndex];
    
    if (!newEntry.note.trim() && newEntry.actions.length === 0 && newEntry.images.length === 0) {
      wx.showToast({
        title: '请输入内容',
        icon: 'none'
      });
      return;
    }
    
    if (!targetPlant) {
      wx.showToast({
        title: '请选择植物',
        icon: 'none'
      });
      return;
    }
    
    wx.showLoading({ title: '保存中...' });
    
    try {
      const entryData = {
        date: new Date().toLocaleDateString('zh-CN'),
        actions: newEntry.actions,
        note: newEntry.note || '无备注',
        images: newEntry.images
      };
      
      // 使用选中的植物 ID
      const newEntryResult = await PlantAPI.addDiaryEntry(targetPlant.id, entryData);
      
      // 更新选中植物的日记列表
      const updatedPlants = [...plants];
      updatedPlants[selectedPlantIndex].diaryEntries.unshift(newEntryResult);
      
      this.setData({
        plants: updatedPlants,
        currentPlant: updatedPlants[this.data.currentPlantIndex],
        showAddModal: false
      });
      
      wx.hideLoading();
      wx.showToast({
        title: '添加成功',
        icon: 'success'
      });
    } catch (error) {
      wx.hideLoading();
      wx.showToast({
        title: '添加失败',
        icon: 'none'
      });
      console.error('添加日记失败:', error);
    }
  },

  onTouchStart: function (e) {
    this.setData({
      touchStartX: e.touches[0].clientX,
      touchStartY: e.touches[0].clientY,
      currentSwipeId: e.currentTarget.dataset.id
    });
  },

  onTouchMove: function (e) {
    const { touchStartX, touchStartY, currentSwipeId, currentPlant } = this.data;
    const touchMoveX = e.touches[0].clientX;
    const touchMoveY = e.touches[0].clientY;
    
    const deltaX = touchMoveX - touchStartX;
    const deltaY = touchMoveY - touchStartY;
    
    if (Math.abs(deltaX) < Math.abs(deltaY)) {
      return;
    }
    
    const entries = currentPlant.diaryEntries.map(entry => {
      if (entry.id === currentSwipeId) {
        let swipeX = deltaX;
        swipeX = Math.max(-80, Math.min(0, swipeX));
        return { ...entry, swipeX };
      }
      return { ...entry, swipeX: 0 };
    });
    
    this.setData({
      'currentPlant.diaryEntries': entries
    });
  },

  onTouchEnd: function (e) {
    const { currentPlant } = this.data;
    
    const entries = currentPlant.diaryEntries.map(entry => {
      if (entry.swipeX < -40) {
        return { ...entry, swipeX: -80 };
      }
      return { ...entry, swipeX: 0 };
    });
    
    this.setData({
      'currentPlant.diaryEntries': entries
    });
  },

  deleteEntry: async function (e) {
    const entryId = e.currentTarget.dataset.id;
    const { currentPlant, currentPlantIndex, plants } = this.data;
    
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条日记吗？',
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '删除中...' });
          
          try {
            await PlantAPI.deleteDiaryEntry(currentPlant.id, entryId);
            
            const updatedPlants = [...plants];
            updatedPlants[currentPlantIndex].diaryEntries = 
              updatedPlants[currentPlantIndex].diaryEntries.filter(e => e.id !== entryId);
            
            this.setData({
              plants: updatedPlants,
              currentPlant: updatedPlants[currentPlantIndex]
            });
            
            wx.hideLoading();
            wx.showToast({
              title: '删除成功',
              icon: 'success'
            });
          } catch (error) {
            wx.hideLoading();
            wx.showToast({
              title: '删除失败',
              icon: 'none'
            });
          }
        }
      }
    });
  },

  previewImage: function (e) {
    const current = e.currentTarget.dataset.src;
    const urls = e.currentTarget.dataset.urls;
    
    wx.previewImage({
      current: current,
      urls: urls
    });
  }
});
