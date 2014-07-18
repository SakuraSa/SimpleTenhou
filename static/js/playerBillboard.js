var get_st_list = function(label){
  var desc=true;
  if(label=="rank_avg" || label=="loser_avg") desc=false;
  lst = [];
  for(var name in st_dic){
    var obj = {};
    obj.name = name;
    obj.value = st_dic[name][label];
    lst.push(obj);
  }
  lst.sort(function(a, b){
    if(desc) return b.value - a.value;
    else return a.value - b.value;
  });
  return lst
};

var option={};
var set_option = function(st_list, title){
  var labels = [];
  var datas = [];
  for(var i=0;i<st_list.length;i++){
    labels.push(st_list[i].name);
    datas.push(st_list[i].value);
  }
  option = {
  title : {
      text: title
  },
  tooltip : {
      trigger: 'axis'
  },
  legend: {
      data:[title]
  },
  toolbox: {
      show : true,
      feature : {
          mark : {show: true},
          dataView : {show: true, readOnly: true},
          magicType : {show: true, type: ['line', 'bar']},
          restore : {show: true},
          saveAsImage : {show: true},
          dataZoom : {show: true}
      }
  },
  xAxis : [
      {
          type : 'category',
          boundaryGap : false,
          data : labels
      }
  ],
  yAxis : [
      {
          type : 'value'
      }
  ],
  series : [
      {
          name:title,
          type:'bar',
          data:datas,
          markLine : {
              data : [
                  {type : 'average', name: '平均值'}
              ]
          }
      }
  ],
  dataZoom : {
    show: true,
    start : 0,
    end : 100
  }
  };
};

var showChart = function(){
  if(option){
    var myChart = echarts.init(document.getElementById('chart'));
    myChart.setOption(option);
  }
};

var showTable = function(st_list){
  var table = $('table#table');
  table.empty();
  if($(':radio[checked]').attr('value')!='aspect_cnt'){
    table.append(
      $('<thead></thead>').append($('<th>排名</th>'))
                          .append($('<th>名称</th>'))
                          .append($('<th>数值</th>'))
    );
    for(var i=0;i<st_list.length;i++){
      var row = st_list[i];
      var playerHref = '/playerView?id_game=' + id_game + '&name=' + row.name;
      table.append(
        $('<tr></tr>').append($('<td></td>').html((i + 1) + ""))
                      .append($('<td></td>').append($('<a></a>').text(row.name).attr('href', playerHref)))
                      .append($('<td></td>').html(row.value))
      );
    }
  }else{
    table.append(
      $('<thead></thead>').append($('<th>排名</th>'))
                          .append($('<th>名称</th>'))
                          .append($('<th>成就点</th>'))
                          .append($('<th>详情</th>'))
    );
    for(var i=0;i<st_list.length;i++){
      var row = st_list[i];
      var playerHref = '/playerView?id_game=' + id_game + '&name=' + row.name;
      var trow = $('<tr></tr>').append($('<td></td>').html((i + 1) + ""))
                               .append($('<td></td>').append($('<a></a>').text(row.name).attr('href', playerHref)))
                               .append($('<td></td>').html(row.value));
      var td_aspect = $('<td></td>');
      var aspect_list = st_dic[st_list[i].name].aspect_list;
      if(aspect_list){
        aspect_list.sort(function(a, b){
          return b.weight - a.weight;
        });
        for(var j=0;j<aspect_list.length;j++){
          var aspect = aspect_list[j];
          var logHref = "/log?ref=" + aspect.ref;
          if(aspect.ref)
            td_aspect.append(
              $('<abbr></abbr>').attr('title', aspect.des).append(
                $('<a></a>').attr('href', logHref).append(aspect.title).append(
                  $('<span class="badge"></span>').append(aspect.weight)
                )
              )
            ).append($('<br>'));
          else
            td_aspect.append(
              $('<abbr></abbr>').attr('title', aspect.des).append(
                $('<a></a>').append(aspect.title).append(
                  $('<span class="badge"></span>').append(aspect.weight)
                )
              )
            ).append($('<br>'));
        }
        trow.append(td_aspect);
      }else{
        trow.append($('<td>无成就</td>'));
      }
      table.append(trow);
    }
  }
};

var toggle_chart = function(){
  var selected = $(':radio[checked]');
  var lst = get_st_list(selected.attr('value'));
  set_option(lst, selected.attr('alt'));
  showChart();
  showTable(lst);
};

$(document).ready(toggle_chart);
$(window).resize(toggle_chart);
$(':radio').on('toggle', toggle_chart);