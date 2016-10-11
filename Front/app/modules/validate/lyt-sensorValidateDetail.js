//radio
define([
  'jquery',
  'underscore',
  'backbone',
  'marionette',
  'sweetAlert',
  'translater',
  'moment',

  'ns_modules/ns_com',
  'ns_map/ns_map',
  'ns_form/NSFormsModuleGit',
  'ns_grid/grid.view'

], function(
  $, _, Backbone, Marionette, Swal, Translater, moment,
  Com, NsMap, NsForm, GridView
){

  'use strict';

  return Marionette.LayoutView.extend({
    template: 'app/modules/validate/templates/tpl-sensorValidateDetail.html',

    className: 'full-height animated white',

    events: {
      'change select#frequency': 'updateFrequency',
      'click .js-btn-validate': 'validate',
    },

    ui: {
      'map': '#map',

      'individualForm': '.js-individual-form',
      'sensorForm': '.js-sensor-form',
    },

    regions: {
      'rgGrid': '.js-rg-grid'
    },

    initialize: function(options) {
      this.model = new Backbone.Model();

      this.com = new Com();

      var datasetInfos = options.dataset.split('_');

      if(datasetInfos.length != 3){
        
      }
      
      this.model.set('type', options.type);

      this.model.set('FK_Sensor', datasetInfos[0]);
      this.model.set('FK_Individual', datasetInfos[1]);
      this.model.set('FK_ptt', datasetInfos[2]);
      

      //this.frequency = options.frequency;
      
    },

    onShow: function(){
      this.displayMap();
      this.displayIndForm();
      this.displaySensorForm();
      this.displayGrid();
    },

    displayMap: function() {
      var url = 'sensors/' + this.model.get('type') + '/uncheckedDatas/' + this.model.get('FK_Individual') + '/' + this.model.get('FK_ptt') + '?geo=true';
      this.map = new NsMap({
        url: url,
        selection: true,
        cluster: true,
        com: this.com,
        zoom: 7,
        element: 'map',
        bbox: true
      });
    },

    displayIndForm: function() {
      this.nsform = new NsForm({
        name: 'IndivForm',
        buttonRegion: [],
        modelurl: 'individuals',
        formRegion: this.ui.individualForm,
        displayMode: 'display',
        id: this.model.get('FK_Individual'),
        reloadAfterSave: false,
      });
    },

    displaySensorForm: function() {
      this.nsform = new NsForm({
        name: 'sensorForm',
        buttonRegion: [],
        modelurl: 'sensors',
        formRegion: this.ui.sensorForm,
        displayMode: 'display',
        id: this.model.get('FK_Sensor'),
        reloadAfterSave: false,
      });
    },

    displayGrid: function(){
      var _this = this;

      var columnDefs = [{
        field: 'date',
        headerName: 'DATE',
        minWidth: 200,
      }, {
        field: 'PK_id',
        headerName: 'PK_id',
        hide: false,
      }, {
        field: 'lat',
        headerName: 'LAT',
      }, {
        field: 'lon',
        headerName: 'LON',
      }, {
        field: 'ele',
        headerName: 'ELE (m)',
      }, {
        field: 'dist',
        headerName: 'DIST (km)',
      }, {
        field: 'speed',
        headerName: 'SPEED (km/h)',
      },{
        field: 'type',
        headerName: 'Type',
      }];

      this.rgGrid.show(this.gridView = new GridView({
        columns: columnDefs,
        com: this.com,
        url: 'sensors/' + this.model.get('type') + '/uncheckedDatas/' + this.model.get('FK_Individual') + '/' + this.model.get('FK_ptt'),
        //afterFirstRowFetch: afterFirstRowFetch,
        clientSide: true,        
        idName: 'PK_id',
        gridOptions: {
          rowSelection: 'multiple',
          enableFilter: true,
          onRowClicked: function(row){
            _this.gridView.interaction('focus', row.data.PK_id || row.data.id);
          }
        },
      }));
    },

    onRender: function() {
      this.$el.i18n();
    },

    //initialize the frequency
    initFrequency: function() {
      if (this.frequency) {
        this.ui.frequency.find('option[value="' + this.frequency + '"]').prop('selected', true);
      }else {
        this.frequency = this.ui.frequency.val();
      }
      this.perHour(this.frequency);
    },

    roundDate: function(date, duration) {
      return moment(Math.floor((+date) / (+duration)) * (+duration));
    },

    clone: function() {
      this.origin = this.grid.collection.fullCollection.clone();
    },

    perHour: function(frequency) {
      this.grid.interaction('resetAll');
      var _this = this;

      if (frequency != 'all') {
        frequency = parseInt(frequency);
        var col0 = this.origin.at(0);

        var date = new moment(col0.get('date'),'DD/MM/YYYY HH:mm:ss');
        var groups = this.origin.groupBy(function(model) {
          var curr = new moment(model.get('date'),'DD/MM/YYYY HH:mm:ss');
          return _this.roundDate(curr, moment.duration(frequency, 'minutes'));
        });
        var ids = [];
        var i = 0;
        for (var rangeDate in groups) {
          var curLength = groups[rangeDate].length;
          var tmp = groups[rangeDate][curLength - 1].get('PK_id');
          ids.push(tmp);
        }
        this.grid.interaction('selectionMultiple', ids);
      } else {
        var ids = this.grid.collection.fullCollection.pluck('PK_id');
        this.grid.interaction('selectionMultiple', ids);
      }
    },

    updateFrequency: function(e) {
      var frequency = $(e.target).val();
      if (!isNaN(frequency))
      this.perHour(frequency);
    },


    validate: function() {
      var _this = this;
      var url = 'sensors/' + this.model.get('type') + '/uncheckedDatas/' + this.model.get('FK_Individual') + '/' + this.model.get('FK_ptt');
      var selectedNodes = this.gridView.gridOptions.api.getSelectedNodes();
      if(!selectedNodes.length){
        return;
      }

      var selectedIds = selectedNodes.map(function(node){
        return node.data.PK_id;
      });
      

      $.ajax({
        url: url,
        method: 'POST',
        data: {data: JSON.stringify(selectedIds)},
        context: this,
      }).done(function(resp) {
        if (resp.errors) {
          resp.title = 'An error occured';
          resp.type = 'error';
        }else {
          resp.title = 'Success';
          resp.type = 'success';
        }

        var callback = function() {
          //_this.navbar.navigateNext();
        };
        resp.text = 'existing: ' + resp.existing + ', inserted: ' + resp.inserted + ', errors:' + resp.errors;
        this.swal(resp, resp.type, callback);
      }).fail(function(resp) {
        this.swal(resp, 'error');
      });
    },

    swal: function(opt, type, callback) {
      var btnColor;
      switch (type){
        case 'success':
          btnColor = 'green';
          break;
        case 'error':
          btnColor = 'rgb(147, 14, 14)';
          break;
        case 'warning':
          btnColor = 'orange';
          break;
        default:
          return;
          break;
      }

      Swal({
        title: opt.title || opt.responseText || 'error',
        text: opt.text || '',
        type: type,
        showCancelButton: false,
        confirmButtonColor: btnColor,
        confirmButtonText: 'OK',
        closeOnConfirm: true,
      },
      function(isConfirm) {
        //could be better
        if (callback) {
          callback();
        }
      });
    },

  });
});
