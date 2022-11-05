// Chart 
$("document").ready(function () {
  $(".GaugeMeter").gaugeMeter();

  // Initially the compliance percentage is set to zero 
  $("#GaugeMeter_10").gaugeMeter({
    percent: 0,
  });

  // Populate the table using previous scan results 
  var table = $("#mTable").DataTable({
    "bInfo": false,
    "paging": false,
    "ordering": false,
    "searching": false,
    ajax: {
      url: "/previous/scan/status",
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

  // Adjust the Gauge meter percentage visualization based on the value received from the previous scan results 
  $.get("/previous/scan/status", function (data) {
    $("#GaugeMeter_10").gaugeMeter({
      percent: data["data"][4][2],
    });
  });

});
