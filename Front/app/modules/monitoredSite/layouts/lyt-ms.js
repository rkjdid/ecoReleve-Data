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

	'./lyt-ms-details'

], function($, _, Backbone, Marionette, Swal, Translater, config,
	Com, NsGrid, NsFilter, LytMsDetail
){

	'use strict';

	return Marionette.LayoutView.extend({
		/*===================================================
		=            Layout Stepper Orchestrator            =
		===================================================*/

		template: 'app/modules/monitoredSite/templates/tpl-ms.html',
		className: 'full-height animated white rel',

		events : {
			'click #btnFilter' : 'filter',
			'click #back' : 'hideDetails',
			'click button#clear' : 'clearFilter'
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
				this.detail.show(new LytMsDetail({id : this.options.id}));
				this.ui.detail.removeClass('hidden');
			}
		},

		displayGrid: function(){
			var _this = this;
			this.grid = new NsGrid({
				pageSize: 13,
				pagingServerSide: true,
				com: this.com,
				url: config.coreUrl+'monitoredSite/',
				urlParams : this.urlParams,
				rowClicked : true,
				totalElement : 'monitoredSite-count',
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

					/*window.app.temp = this;

					_this.totalEntries(this.grid);
					var rows = this.grid.body.rows;
					if(_this.currentRow){
						for (var i = 0; i < rows.length; i++) {
							if(rows[i].model.attributes.ID == _this.currentRow.model.attributes.ID){
								_this.currentRow = rows[i];
								rows[i].$el.addClass('active');
								return rows[i];
							}
						}
					}else{
						var row = this.grid.body.rows[0];
						if(row){
							_this.currentRow = row;
							row.$el.addClass('active');
						}
					}*/
				}
			});

			this.grid.rowClicked = function(args){
				_this.rowClicked(args.row);
			};
			this.grid.rowDbClicked = function(args){
				_this.rowDbClicked(args.row);
			};
			this.ui.grid.html(this.grid.displayGrid());
			this.ui.paginator.html(this.grid.displayPaginator());
		},

		displayFilter: function(){
			this.filters = new NsFilter({
				url: config.coreUrl + 'monitoredSite/',
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
			this.detail.show(new LytMsDetail({id : id}));
			this.ui.detail.removeClass('hidden');

			Backbone.history.navigate('monitoredSite/'+id, {trigger: false})
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
	});
});