function format(d) {
    return (
      '<table cellpadding="5" cellspacing="0" border="0" style="padding-left:50px;">' +
      "<td>Project:</td>" +
      "<td>" +
      d.project +
      "</td>" +
      "</tr>" +
      "<tr>" +
      "<td>Repository:</td>" +
      "<td>" +
      d.repository +
      "</td>" +
      "</tr>" +
      "<tr>" +
      "<td>Number of secrets:</td>" +
      "<td>" +
      d.secretscount +
      "</td>" +
      "</tr>" +
      "<tr>" +
      "<td>Last committer name:</td>" +
      "<td>" +
      d.lastcommitname +
      "</td>" +
      "</tr>" +
      "<tr>" +
      "<td>Last committer email:</td>" +
      "<td>" +
      d.lastcommitemail +
      "</td>" +
      "</tr>" +
      "<tr>" +
      "<td>Last commit date:</td>" +
      "<td>" +
      d.lastcommitdate +
      "</td>" +
      "</tr>" +
      "<tr>" +
      "</table>"
    );
  }
  
  $(document).ready(function () {
    var table = $("#mTable").DataTable({
      ajax: {
        url: "/scan/analysis",
        dataType: "json",
        type: "get",
        async: false,
        //data:{'type': 'admin'},
        done: function (data) {
          JSON.parse(data);
          return data;
        },
        fail: function (d) {
          //console.log("error");
          alert("404. Please wait until the File is Loaded.");
        },
      },
      columns: [
        {
          className: "details-control",
          orderable: false,
          ajax: "exp",
          defaultContent: "",
        },
        { ajax: "project" },
        { ajax: "repository" },
        { ajax: "secretscount" },
        { ajax: "lastcommitdate" },
      ],
      order: [[4, "asc"]],
    });

    // Add event listener for opening and closing details
    $("#mTable tbody").on("click", "td.details-control", function () {
      var tr = $(this).closest("tr");
      var row = table.row(tr);
  
      if (row.child.isShown()) {
        // This row is already open - close it
        row.child.hide();
        tr.removeClass("shown");
      } else {
        // Open this row
        console.log(row.data())
  
        var rowdetails = $.ajax({
          url: "/scan/analysis/record",
          type: "get", //send it through get method
          dataType: "json",
          async: false,
          data: {
            q: JSON.stringify(row.data()),
          },
          done: function (response) {
            //      JSON.parse(response);
            //console.log(response);
            return response;
          },
          fail: function (xhr) {
            //console.log("error");
          },
        });
  
        rowdetails = rowdetails["responseJSON"];
        console.log(rowdetails);
  
        row.child(format(rowdetails)).show();
        tr.addClass("shown");
      }
    });
  
    // Handle click on "Expand All" button
    $("#btn-show-all-children").on("click", function () {
      // Enumerate all rows
      table.rows().every(function () {
        // If row has details collapsed
        if (!this.child.isShown()) {
          // Open this row
          this.child(format(this.data())).show();
          $(this.node()).addClass("shown");
        }
      });
    });
  
    // Handle click on "Collapse All" button
    $("#btn-hide-all-children").on("click", function () {
      // Enumerate all rows
      table.rows().every(function () {
        // If row has details expanded
        if (this.child.isShown()) {
          // Collapse row details
          this.child.hide();
          $(this.node()).removeClass("shown");
        }
      });
    });
  });
  