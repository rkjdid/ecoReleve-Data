//radio
define([
	'jquery',
	'underscore',
	'backbone',
	'marionette',
	'sweetAlert',
	'translater',
	'config',
	'ns_modules/ns_com',
	'ns_grid/model-grid',
	'ns_filter/model-filter',

	//'./lyt-indiv-details' 

], function($, _, Backbone, Marionette, Swal, Translater, config,
	Com, NsGrid, NsFilter//, LytIndivDetail
){

	'use strict';

	return Marionette.LayoutView.extend({
		/*===================================================
		=            Layout Stepper Orchestrator            =
		===================================================*/

		template: 'app/modules/sensor/templates/tpl-sensor.html',
		className: 'full-height animated white rel',

		events : {
			'click #btnFilter' : 'filter',
			'click #back' : 'hideDetails',
			'click button#clear' : 'clearFilter',
			'change select.FK_SensorType' : 'updateModels'
		},

		ui: {
			'grid': '#grid',
			'paginator': '#paginator',
			'filter': '#filter',
			'detail': '#detail',
			'totalEntries': '#totalEntries',
		},

		regions: {
			detail : '#detail'
		},

		initialize: function(options){
			this.translater = Translater.getTranslater();
			this.com = new Com();

		},

		onRender: function(){

			this.$el.i18n();
		},

		onShow : function(){
			this.displayFilter();
			this.displayGrid(); 
			if(this.options.id){
				this.detail.show(new LytSensorDetail({id : this.options.id}));
				this.ui.detail.removeClass('hidden');
			}
		},

		displayGrid: function(){
			var _this = this;
			this.grid = new NsGrid({
				pageSize: 13,
				pagingServerSide: true,
				com: this.com,
				url: config.coreUrl+'sensors/',
				urlParams : this.urlParams,
				rowClicked : true,
				totalElement : 'sensor-count',
				onceFetched: function(params){
					var listPro = {};
					var idList  = [];
					this.collection.each(function(model){
						idList.push(model.get('ID'));
					});
					idList.sort();
					listPro.idList = idList;
					listPro.minId = idList[0];
					listPro.maxId = idList [(idList.length - 1)];
					listPro.state = this.collection.state;
					listPro.criteria = $.parseJSON(params.criteria);
					window.app.listProperties = listPro ;
					_this.totalEntries(this.grid);
				}
			});

			this.grid.rowClicked = function(row){
				_this.rowClicked(row);
			};
			this.grid.rowDbClicked = function(row){
				_this.rowDbClicked(row);
			};
			this.ui.grid.html(this.grid.displayGrid());
			this.ui.paginator.html(this.grid.displayPaginator());
		},

		displayFilter: function(){
			this.filters = new NsFilter({
				url: config.coreUrl + 'sensors/',
				com: this.com,
				filterContainer: 'filter',
			});
		},

		filter: function(){
			this.filters.update();
		},
		clearFilter : function(){
			this.filters.reset();
		},
		rowClicked: function(row){
			var id = row.model.get('ID');
			//this.detail.show(new LytIndivDetail({id : id}));
			//this.ui.detail.removeClass('hidden');

			//Backbone.history.navigate('sensor/'+id, {trigger: false})
		},

		rowDbClicked: function(row){

		},
		hideDetails : function(){
			this.ui.detail.addClass('hidden');
		},
		totalEntries: function(grid){
			this.total = grid.collection.state.totalRecords;
			this.ui.totalEntries.html(this.total);
		},
		updateModels : function(e){
			// get list of models for selected sensor type
			var selectedType = $(e.target).val();
			var modelField = $('select.Model');
			var url  = config.coreUrl + 'sensors/getModels?sensorType=' + selectedType;
			$.ajax({
				url: url,
				context: this,
				}).done(function(data) {
					this.updateField(data,modelField);
				}
			);
			this.updateCompany(selectedType);
		},
		updateCompany : function(selectedType){
			var companyField = $('select.Compagny');
			var url  = config.coreUrl + 'sensors/getCompany?sensorType=' + selectedType;
			$.ajax({
				url: url,
				context: this,
				}).done(function(data) {
					this.updateField(data,companyField);
				}
			);
		},
		updateField : function(data, elem){
			var content = '<option></option>';
			for (var i=0;i<data.length;i++){
					content += '<option>'+ data[i] +'</option>';
			}
			$(elem).html(content);
		}
	});
});
