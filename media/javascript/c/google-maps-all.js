
function MarkerManager(map,opt_opts){var me=this;me.map_=map;me.mapZoom_=map.getZoom();me.projection_=map.getCurrentMapType().getProjection();opt_opts=opt_opts||{};me.tileSize_=MarkerManager.DEFAULT_TILE_SIZE_;var maxZoom=MarkerManager.DEFAULT_MAX_ZOOM_;if(opt_opts.maxZoom!=undefined){maxZoom=opt_opts.maxZoom;}
me.maxZoom_=maxZoom;me.trackMarkers_=opt_opts.trackMarkers;var padding;if(typeof opt_opts.borderPadding=="number"){padding=opt_opts.borderPadding;}else{padding=MarkerManager.DEFAULT_BORDER_PADDING_;}
me.swPadding_=new GSize(-padding,padding);me.nePadding_=new GSize(padding,-padding);me.borderPadding_=padding;me.gridWidth_=[];me.grid_=[];me.grid_[maxZoom]=[];me.numMarkers_=[];me.numMarkers_[maxZoom]=0;GEvent.bind(map,"moveend",me,me.onMapMoveEnd_);me.removeOverlay_=function(marker){map.removeOverlay(marker);me.shownMarkers_--;};me.addOverlay_=function(marker){map.addOverlay(marker);me.shownMarkers_++;};me.resetManager_();me.shownMarkers_=0;me.shownBounds_=me.getMapGridBounds_();};MarkerManager.DEFAULT_TILE_SIZE_=1024;MarkerManager.DEFAULT_MAX_ZOOM_=17;MarkerManager.DEFAULT_BORDER_PADDING_=100;MarkerManager.MERCATOR_ZOOM_LEVEL_ZERO_RANGE=256;MarkerManager.prototype.resetManager_=function(){var me=this;var mapWidth=MarkerManager.MERCATOR_ZOOM_LEVEL_ZERO_RANGE;for(var zoom=0;zoom<=me.maxZoom_;++zoom){me.grid_[zoom]=[];me.numMarkers_[zoom]=0;me.gridWidth_[zoom]=Math.ceil(mapWidth/me.tileSize_);mapWidth<<=1;}};MarkerManager.prototype.clearMarkers=function(){var me=this;me.processAll_(me.shownBounds_,me.removeOverlay_);me.resetManager_();};MarkerManager.prototype.getTilePoint_=function(latlng,zoom,padding){var pixelPoint=this.projection_.fromLatLngToPixel(latlng,zoom);return new GPoint(Math.floor((pixelPoint.x+padding.width)/this.tileSize_),Math.floor((pixelPoint.y+padding.height)/this.tileSize_));};MarkerManager.prototype.addMarkerBatch_=function(marker,minZoom,maxZoom){var mPoint=marker.getPoint();if(this.trackMarkers_){GEvent.bind(marker,"changed",this,this.onMarkerMoved_);}
var gridPoint=this.getTilePoint_(mPoint,maxZoom,GSize.ZERO);for(var zoom=maxZoom;zoom>=minZoom;zoom--){var cell=this.getGridCellCreate_(gridPoint.x,gridPoint.y,zoom);cell.push(marker);gridPoint.x=gridPoint.x>>1;gridPoint.y=gridPoint.y>>1;}};MarkerManager.prototype.isGridPointVisible_=function(point){var me=this;var vertical=me.shownBounds_.minY<=point.y&&point.y<=me.shownBounds_.maxY;var minX=me.shownBounds_.minX;var horizontal=minX<=point.x&&point.x<=me.shownBounds_.maxX;if(!horizontal&&minX<0){var width=me.gridWidth_[me.shownBounds_.z];horizontal=minX+width<=point.x&&point.x<=width-1;}
return vertical&&horizontal;}
MarkerManager.prototype.onMarkerMoved_=function(marker,oldPoint,newPoint){var me=this;var zoom=me.maxZoom_;var changed=false;var oldGrid=me.getTilePoint_(oldPoint,zoom,GSize.ZERO);var newGrid=me.getTilePoint_(newPoint,zoom,GSize.ZERO);while(zoom>=0&&(oldGrid.x!=newGrid.x||oldGrid.y!=newGrid.y)){var cell=me.getGridCellNoCreate_(oldGrid.x,oldGrid.y,zoom);if(cell){if(me.removeFromArray(cell,marker)){me.getGridCellCreate_(newGrid.x,newGrid.y,zoom).push(marker);}}
if(zoom==me.mapZoom_){if(me.isGridPointVisible_(oldGrid)){if(!me.isGridPointVisible_(newGrid)){me.removeOverlay_(marker);changed=true;}}else{if(me.isGridPointVisible_(newGrid)){me.addOverlay_(marker);changed=true;}}}
oldGrid.x=oldGrid.x>>1;oldGrid.y=oldGrid.y>>1;newGrid.x=newGrid.x>>1;newGrid.y=newGrid.y>>1;--zoom;}
if(changed){me.notifyListeners_();}};MarkerManager.prototype.removeMarker=function(marker){var me=this;var zoom=me.maxZoom_;var changed=false;var point=marker.getPoint();var grid=me.getTilePoint_(point,zoom,GSize.ZERO);while(zoom>=0){var cell=me.getGridCellNoCreate_(grid.x,grid.y,zoom);if(cell){me.removeFromArray(cell,marker);}
if(zoom==me.mapZoom_){if(me.isGridPointVisible_(grid)){me.removeOverlay_(marker);changed=true;}}
grid.x=grid.x>>1;grid.y=grid.y>>1;--zoom;}
if(changed){me.notifyListeners_();}};MarkerManager.prototype.addMarkers=function(markers,minZoom,opt_maxZoom){var maxZoom=this.getOptMaxZoom_(opt_maxZoom);for(var i=markers.length-1;i>=0;i--){this.addMarkerBatch_(markers[i],minZoom,maxZoom);}
this.numMarkers_[minZoom]+=markers.length;};MarkerManager.prototype.getOptMaxZoom_=function(opt_maxZoom){return opt_maxZoom!=undefined?opt_maxZoom:this.maxZoom_;}
MarkerManager.prototype.getMarkerCount=function(zoom){var total=0;for(var z=0;z<=zoom;z++){total+=this.numMarkers_[z];}
return total;};MarkerManager.prototype.addMarker=function(marker,minZoom,opt_maxZoom){var me=this;var maxZoom=this.getOptMaxZoom_(opt_maxZoom);me.addMarkerBatch_(marker,minZoom,maxZoom);var gridPoint=me.getTilePoint_(marker.getPoint(),me.mapZoom_,GSize.ZERO);if(me.isGridPointVisible_(gridPoint)&&minZoom<=me.shownBounds_.z&&me.shownBounds_.z<=maxZoom){me.addOverlay_(marker);me.notifyListeners_();}
this.numMarkers_[minZoom]++;};GBounds.prototype.containsPoint=function(point){var outer=this;return(outer.minX<=point.x&&outer.maxX>=point.x&&outer.minY<=point.y&&outer.maxY>=point.y);}
MarkerManager.prototype.getGridCellCreate_=function(x,y,z){var grid=this.grid_[z];if(x<0){x+=this.gridWidth_[z];}
var gridCol=grid[x];if(!gridCol){gridCol=grid[x]=[];return gridCol[y]=[];}
var gridCell=gridCol[y];if(!gridCell){return gridCol[y]=[];}
return gridCell;};MarkerManager.prototype.getGridCellNoCreate_=function(x,y,z){var grid=this.grid_[z];if(x<0){x+=this.gridWidth_[z];}
var gridCol=grid[x];return gridCol?gridCol[y]:undefined;};MarkerManager.prototype.getGridBounds_=function(bounds,zoom,swPadding,nePadding){zoom=Math.min(zoom,this.maxZoom_);var bl=bounds.getSouthWest();var tr=bounds.getNorthEast();var sw=this.getTilePoint_(bl,zoom,swPadding);var ne=this.getTilePoint_(tr,zoom,nePadding);var gw=this.gridWidth_[zoom];if(tr.lng()<bl.lng()||ne.x<sw.x){sw.x-=gw;}
if(ne.x-sw.x+1>=gw){sw.x=0;ne.x=gw-1;}
var gridBounds=new GBounds([sw,ne]);gridBounds.z=zoom;return gridBounds;};MarkerManager.prototype.getMapGridBounds_=function(){var me=this;return me.getGridBounds_(me.map_.getBounds(),me.mapZoom_,me.swPadding_,me.nePadding_);};MarkerManager.prototype.onMapMoveEnd_=function(){var me=this;me.objectSetTimeout_(this,this.updateMarkers_,0);};MarkerManager.prototype.objectSetTimeout_=function(object,command,milliseconds){return window.setTimeout(function(){command.call(object);},milliseconds);};MarkerManager.prototype.refresh=function(){var me=this;if(me.shownMarkers_>0){me.processAll_(me.shownBounds_,me.removeOverlay_);}
me.processAll_(me.shownBounds_,me.addOverlay_);me.notifyListeners_();};MarkerManager.prototype.updateMarkers_=function(){var me=this;me.mapZoom_=this.map_.getZoom();var newBounds=me.getMapGridBounds_();if(newBounds.equals(me.shownBounds_)&&newBounds.z==me.shownBounds_.z){return;}
if(newBounds.z!=me.shownBounds_.z){me.processAll_(me.shownBounds_,me.removeOverlay_);me.processAll_(newBounds,me.addOverlay_);}else{me.rectangleDiff_(me.shownBounds_,newBounds,me.removeCellMarkers_);me.rectangleDiff_(newBounds,me.shownBounds_,me.addCellMarkers_);}
me.shownBounds_=newBounds;me.notifyListeners_();};MarkerManager.prototype.notifyListeners_=function(){GEvent.trigger(this,"changed",this.shownBounds_,this.shownMarkers_);};MarkerManager.prototype.processAll_=function(bounds,callback){for(var x=bounds.minX;x<=bounds.maxX;x++){for(var y=bounds.minY;y<=bounds.maxY;y++){this.processCellMarkers_(x,y,bounds.z,callback);}}};MarkerManager.prototype.processCellMarkers_=function(x,y,z,callback){var cell=this.getGridCellNoCreate_(x,y,z);if(cell){for(var i=cell.length-1;i>=0;i--){callback(cell[i]);}}};MarkerManager.prototype.removeCellMarkers_=function(x,y,z){this.processCellMarkers_(x,y,z,this.removeOverlay_);};MarkerManager.prototype.addCellMarkers_=function(x,y,z){this.processCellMarkers_(x,y,z,this.addOverlay_);};MarkerManager.prototype.rectangleDiff_=function(bounds1,bounds2,callback){var me=this;me.rectangleDiffCoords(bounds1,bounds2,function(x,y){callback.apply(me,[x,y,bounds1.z]);});};MarkerManager.prototype.rectangleDiffCoords=function(bounds1,bounds2,callback){var minX1=bounds1.minX;var minY1=bounds1.minY;var maxX1=bounds1.maxX;var maxY1=bounds1.maxY;var minX2=bounds2.minX;var minY2=bounds2.minY;var maxX2=bounds2.maxX;var maxY2=bounds2.maxY;for(var x=minX1;x<=maxX1;x++){for(var y=minY1;y<=maxY1&&y<minY2;y++){callback(x,y);}
for(var y=Math.max(maxY2+1,minY1);y<=maxY1;y++){callback(x,y);}}
for(var y=Math.max(minY1,minY2);y<=Math.min(maxY1,maxY2);y++){for(var x=Math.min(maxX1+1,minX2)-1;x>=minX1;x--){callback(x,y);}
for(var x=Math.max(minX1,maxX2+1);x<=maxX1;x++){callback(x,y);}}};MarkerManager.prototype.removeFromArray=function(array,value,opt_notype){var shift=0;for(var i=0;i<array.length;++i){if(array[i]===value||(opt_notype&&array[i]==value)){array.splice(i--,1);shift++;}}
return shift;};(function(){var defaultStyle={tabBar:{background:'#F4F4F4 none repeat scroll 0 0',borderBottom:'1px solid #B0B0B0',padding:'6px 8px 4px',marginRight:'13px',whiteSpace:'nowrap',verticalAlign:'bottom'},tabLeft:{},tabRight:{},tabOn:{background:'#FFFFFF none repeat scroll 0 0',padding:'6px 8px 4px',borderTop:'1px solid #B0B0B0',borderLeft:'1px solid #B0B0B0',borderRight:'1px solid #B0B0B0',borderBottom:'2px solid #FFFFFF',color:'#000000',textDecoration:'none',fontWeight:'bold'},tabOff:{background:'#F4F4F4 none repeat scroll 0 0',padding:'6px 8px 4px',color:'#0000FF',border:'none',textDecoration:'underline',fontWeight:'normal'},content:{borderStyle:'none solid solid solid',borderWidth:'1px',borderColor:'#B0B0B0',borderTop:'none',overflow:'auto'},summary:{overflow:'auto',marginBottom:'5px'}};var setVals=function(obj,vals){if(obj&&vals){for(var x in vals){if(vals.hasOwnProperty(x)){if(obj[x]&&typeof vals[x]==='object'){obj[x]=setVals(obj[x],vals[x]);}else{obj[x]=vals[x];}}}}
return obj;};var createEl=function(tag,attrs,content,style,parent){var node=content;if(!content||(content&&typeof content==='string')){node=document.createElement(tag);node.innerHTML=content||'';}
if(style){setVals(node.style,style);}
if(attrs){setVals(node,attrs);}
if(parent){parent.appendChild(node);}
return node;};var getPosition=function(el,parent){var leftPos=0;var topPos=0;var par=el;while(par&&par!==parent){leftPos+=par.offsetLeft;topPos+=par.offsetTop;par=par.offsetParent;}
return{left:leftPos,top:topPos};};function MaxContentTab(label,content){this.label_=label;this.contentNode_=createEl('div',null,content,null,null);this.navNode_=null;}
MaxContentTab.prototype.getLabel=function(){return this.label_;};MaxContentTab.prototype.getContentNode=function(){return this.contentNode_;};function TabbedMaxContent(iw){this.infoWindow_=iw;GEvent.bind(iw,'maximizeclick',this,this.onMaximizeClick_);GEvent.bind(iw,'restoreclick',this,this.onRestoreClick_);GEvent.bind(iw,'maximizeend',this,this.onMaximizeEnd_);this.style_={};this.maxNode_=null;this.summaryNode_=null;this.navsNode_=null;this.contentsNode_=null;this.tabs_=[];}
TabbedMaxContent.prototype.initialize_=function(sumNode,tabs,opt_maxOptions){this.tabs_=tabs;this.selectedTab_=-1;if(this.maxNode_){GEvent.clearNode(this.maxNode_);this.maxNode_.innerHTML='';}else{this.maxNode_=createEl('div',{id:'maxcontent'});}
opt_maxOptions=opt_maxOptions||{};var selectedTab=opt_maxOptions.selectedTab||0;this.style_=setVals({},defaultStyle);this.style_=setVals(this.style_,opt_maxOptions.style);this.summaryNode_=createEl('div',null,sumNode,this.style_.summary,this.maxNode_);this.navsNode_=createEl('div',null,null,this.style_.tabBar,this.maxNode_);this.contentsNode_=createEl('div',null,null,null,this.maxNode_);if(tabs&&tabs.length){createEl('span',null,null,this.style_.tabLeft,this.navsNode_);for(var i=0,ct=tabs.length;i<ct;i++){if(i===selectedTab||tabs[i].getLabel()===selectedTab){this.selectedTab_=i;}
tabs[i].navNode_=createEl('span',null,tabs[i].getLabel(),this.style_.tabOff,this.navsNode_);var node=createEl('div',null,tabs[i].getContentNode(),this.style_.content,this.contentsNode_);node.style.display='none';}
createEl('span',null,null,this.style_.tabRight,this.navsNode_);}};TabbedMaxContent.prototype.onMaximizeClick_=function(){for(var i=0,ct=this.tabs_.length;i<ct;i++){GEvent.addDomListener(this.tabs_[i].navNode_,'click',GEvent.callback(this,this.selectTab,i));}};TabbedMaxContent.prototype.onRestoreClick_=function(){if(this.maxNode_){GEvent.clearNode(this.maxNode_);}};TabbedMaxContent.prototype.onMaximizeEnd_=function(){this.checkResize();this.selectTab(this.selectedTab_);};TabbedMaxContent.prototype.selectTab=function(identifier){var trigger=false;var hasVisibleTab=false;var tab;for(var i=0,ct=this.tabs_.length;i<ct;i++){tab=this.tabs_[i];if(i===identifier||tab.getLabel()===identifier){if(tab.getContentNode().style.display==='none'){setVals(tab.navNode_.style,this.style_.tabOn);tab.getContentNode().style.display='block';this.selectedTab_=i;trigger=true;}
hasVisibleTab=true;}else{setVals(tab.navNode_.style,this.style_.tabOff);tab.getContentNode().style.display='none';}}
if(trigger){GEvent.trigger(this,'selecttab',this.tabs_[this.selectedTab_]);}
if(!hasVisibleTab){this.selectTab(0);}};TabbedMaxContent.prototype.getTab=function(identifier){for(var i=0,ct=this.tabs_.length;i<ct;i++){if(i===identifier||this.tabs_[i].getLabel()===identifier){return this.tabs_[i];}}};TabbedMaxContent.prototype.checkResize=function(){var container=this.infoWindow_.getContentContainers()[0];var contents=this.contentsNode_;var pos=getPosition(contents,container);for(var i=0,ct=this.tabs_.length;i<ct;i++){var t=this.tabs_[i].getContentNode();t.style.width=container.style.width;t.style.height=(parseInt(container.style.height,10)-pos.top)+'px';}};GMap2.prototype.openMaxContentTabs=function(latlng,minNode,sumNode,tabs,opt_maxOptions){var max=this.getTabbedMaxContent();var opts=opt_maxOptions||{};max.initialize_(sumNode,tabs,opts);opts.maxContent=max.maxNode_;if(opts.style){delete opts.style;}
if(opts.selectedTab){delete opts.selectedTab;}
if(minNode.style){minNode.style.marginTop='6px';}
this.openInfoWindow(latlng,minNode,opts);if(opts.maximized){var iw=this.getInfoWindow();var m=GEvent.addListener(this,'infowindowopen',function(){GEvent.removeListener(m);iw.maximize();});}};GMap2.prototype.openMaxContentTabsHtml=function(latlng,html,summary,tabs,opt_maxOptions){this.openMaxContentTabs(latlng,createEl('div',null,html),createEl('div',null,summary),tabs,opt_maxOptions);};GMap2.prototype.getTabbedMaxContent=function(){this.maxContent_=this.maxContent_||new TabbedMaxContent(this.getInfoWindow());return this.maxContent_;};GMarker.prototype.openMaxContentTabsHtml=function(map,minHtml,summaryHtml,tabs,opt_maxOptions){map.openMaxContentTabsHtml(this.getLatLng(),minHtml,summaryHtml,tabs,opt_maxOptions);};GMarker.prototype.openMaxContentTabs=function(map,minNode,summaryNode,tabs,opt_maxOptions){map.openMaxContentTabs(this.getLatLng(),minNode,summaryNode,tabs,opt_maxOptions);};window.MaxContentTab=MaxContentTab;})();GMap2.prototype.openInfoWindowTabsMaxTabs=function(latlng,tabs,maxTabs,opts)
{var tabbedMaxContent=this.getTabbedMaxContent();opts=opts||{};tabbedMaxContent.initialize_("",maxTabs,opts);opts.maxContent=tabbedMaxContent.maxNode_;this.openInfoWindowTabs(latlng,tabs,opts);};function getMapCenter(map,point_data,initialZoom)
{var baseWidth=Math.abs(map.getBounds().getNorthEast().x)*2;var baseHeight=Math.abs(map.getBounds().getNorthEast().y)*2;var minLat=99999999;var minLng=99999999;var maxLat=-99999999;var maxLng=-99999999;var i;for(i=0;i<point_data.length;i++)
{var lat=point_data[i].lat;var lng=point_data[i].lng;if(lat<minLat)minLat=lat;if(lat>maxLat)maxLat=lat;if(lng<minLng)minLng=lng;if(lng>maxLng)maxLng=lng;}
var wZoom;var w=Math.abs(maxLng-minLng);for(wZoom=initialZoom;wZoom>=0;wZoom--)
{if(baseWidth>w*1.1)
{break;}
baseWidth*=2;}
var hZoom;var h=Math.abs(maxLat-minLat);for(hZoom=initialZoom;hZoom>=0;hZoom--)
{if(baseHeight>h*1.1)
{break;}
baseHeight*=2;}
return{latlng:new GLatLng((minLat+maxLat)/2,(minLng+maxLng)/2),zoom:Math.min(wZoom,hZoom)};}
function initTripMap(id,point_data,bind_events)
{if(!GBrowserIsCompatible())
{return;}
var initialZoom=16;var map=new GMap2(document.getElementById(id));map.addControl(new GLargeMapControl());map.setCenter(new GLatLng(0,0),initialZoom);var mapCenter=getMapCenter(map,point_data,initialZoom);map.setCenter(mapCenter.latlng,mapCenter.zoom);function addListener(overlay,id,i){GEvent.addListener(overlay,'click',function(latlng){var children=$(id).children().clone(true);if(children.length==1){var child=$(children[0]);map.openInfoWindow(latlng,child.find('.short-content')[0],{maxContent:child.find('.full-content')[0]});}else{function tabname(i,j){if(i==0&&point_data[0].place_id==point_data[point_data.length-1].place_id){if(j==0){return"Start";}
if(j==children.length-1){return"End";}}
return ordinal(j+1);}
var tabs=$.map(children,function(c,j){return new GInfoWindowTab(tabname(i,j),$(c).find('.short-content')[0]);});if($.grep(children,function(c){return $(c).find('.full-content').length!=0;}).length==0){map.openInfoWindowTabs(latlng,tabs);}else{var maxTabs=$.map(children,function(c,j){return new MaxContentTab(tabname(i,j),$(c).find('.full-content')[0]);});map.openInfoWindowTabsMaxTabs(latlng,tabs,maxTabs);}}});}
var markers=[];for(var i=0,addedOverlays=[];i<point_data.length;i++)
{if(i+1<point_data.length){var p1=point_data[i];var p2=point_data[i+1];var segment=[Math.min(p1.place_id,p2.place_id),Math.max(p1.place_id,p2.place_id)];if($.inArray(segment,addedOverlays)==-1){var line=new GPolyline([new GLatLng(p1.lat,p1.lng),new GLatLng(p2.lat,p2.lng)],"#ff0000",3);if(bind_events){addListener(line,"#segment-data #place-pair-"+segment[0]+"-"+segment[1],i);}
map.addOverlay(line);addedOverlays.push(segment);}}
var p=point_data[i];if($.inArray(p.place_id,addedOverlays)==-1){var icon=G_DEFAULT_ICON;if(!p.visited){icon=new GIcon(G_DEFAULT_ICON,"/media/images/marker_grey.png");}
if(i==0||i==point_data.length-1){icon=new GIcon(G_DEFAULT_ICON,"/media/images/marker_green.png");}
var marker=new GMarker(new GLatLng(p.lat,p.lng),{title:p.name,icon:icon});if(bind_events){addListener(marker,"#point-data #place-"+p.place_id,i);}
markers.push(marker);addedOverlays.push(p.place_id);}}
setTimeout(function(){var mgr=new MarkerManager(map);mgr.addMarkers(markers,1);mgr.refresh();},0);}
function cleanupMap()
{GUnload();}