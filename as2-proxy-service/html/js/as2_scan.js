$(document).ready(function () {

  // This function handles the scan status
  // Updates the progress bar value and visualization 
  // Updates the table values 
  // It runs every 30 seconds 
  function scanStatus() {
    $.ajax({
      url: "/scan/status",
      success:
        function (data) {
          if ((data['data'][0][2] == 'In Progress') || (data['data'][0][2] == 'Completed')) {
            $("#scan-progress-bar").css("width", data['data'][5][2] + "%");
            $("#scan-progress-bar").text(data['data'][5][2] + " %");
            var datatable = $("#mTable").DataTable();
            datatable.clear();
            datatable.rows.add(data['data']);
            datatable.draw();
          }
        }
    });
  };

  // This function is to handle the page refresh 
  // If the scan is in progress then hides the scan button view and only displays the table values 
  $.ajax({
    url: "/scan/status",
    success:
      function (data) {
        if (data['data'][0][2] == 'In Progress') {
          $('#scansection').hide();
          $('#tablesection').show();
          $("#scan-progress-bar").css("width", data['data'][5][2] + "%");
          $("#scan-progress-bar").text(data['data'][5][2] + " %");
        } else {
          $('#scansection').show();
          $('#tablesection').hide();
        }

      }

  });

  // Table view 
  var table = $("#mTable").DataTable({
    "bInfo": false,
    "paging": false,
    "ordering": false,
    "searching": false,
    ajax: {
      url: "/scan/status",
      dataType: "json",
      type: "get",
      async: false,
      done: function (data) {
        return data["data"];
      },
      fail: function (d) {
        console.log("error");
      },
    },
    columns: [
      { ajax: "srno" },
      { ajax: "name" },
      { ajax: "value" },
    ],
  });


  // Trigger scan 
  $("#scanbutton")
    .unbind()
    .click(function () {
      $("#scanModal").modal("show");
      $("#scan_ok")
        .unbind()
        .click(function () {
          $("#scanModal").modal("hide");
          $('#scansection').hide();
          $('#tablesection').show();
          var scan = $.get("/scan/start", function (returnedData) {
            var datatable = $("#mTable").DataTable();
            datatable.clear();
            $("#scan-progress-bar").css("width", "0%");
            $("#scan-progress-bar").text("0 %");
            datatable.rows.add(returnedData['data']);
            datatable.draw();
          });
        });
      $("#scan_cancel")
        .unbind()
        .click(function () {
          $("#scanModal").modal("hide");
        });
    }); //scan 
  setInterval(scanStatus, 30000);
});