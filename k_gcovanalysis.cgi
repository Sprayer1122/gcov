#!/grid/common/pkgs/perl/v5.12.2/bin/perl

use CGI qw(:standard);
use CGI::Carp qw(warningsToBrowser fatalsToBrowser);

use DBH::dbh qw(getDBH disconnectDBH);
use Data::Dumper;
use List::MoreUtils qw(uniq);
use lib '/lan/fed/etpv/cgi-bin/gcov_failure_reasons/PACKAGES';
use preeti qw(categorizeFromIgnoreFile getGcovOwnerAndReviewer);  #A package where all functions are defined
use Scalar::Util qw(reftype);

print "Content-type: text/html\n\n"; 
my $timestamp=`cat last_update_time | xargs`;
$timestamp =~ s/^\s+|\s+$//g; 

my $all_commands = `ls /lan/fed/etpv/cgi-bin/gcov_failure_reasons/commands | xargs`;
my @all_commands = split(" ",$all_commands);
my $dbh = getDBH();

 $ENV{'REQUEST_METHOD'} =~ tr/a-z/A-Z/;
  if ($ENV{'REQUEST_METHOD'} eq "POST") {
      read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
       } else {
           $buffer = $ENV{'QUERY_STRING'};
            }
### Split information into name/value pairs
    @pairs = split(/&/, $buffer);
    foreach $pair (@pairs) {
        ($name, $value) = split(/=/, $pair);
        $value =~ tr/+/ /;
         $value =~ s/%(..)/pack("C", hex($1))/eg;
         $FORM{$name} = $value;
     }
$build = $FORM{build};
$bucket = $FORM{bucket};
$reason = $FORM{reason};
$command = $FORM{command};
$more_or_less = $FORM{more_or_less};
$analysis_status = $FORM{analysis_status};
$bucket_or_owner = $FORM{bucket_or_owner};

$test = $FORM{test};
if($test eq "" ) { $test="24_10";}


#print "$build $bucket $reason <br>";
#################################################################################################

$getGcovTables = "select TABLE_NAME from INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'gcov_failure_reasons_$test%' AND TABLE_NAME NOT LIKE 'gcov_failure_reasons_%wv' AND TABLE_NAME NOT LIKE '%temp%' ORDER BY UPDATE_TIME DESC ";
 $sth = $dbh->prepare("$getGcovTables");
  $sth->execute() or die $DBI::errstr;

 while (my $row = $sth->fetchrow_hashref()) {
   $temp=$row->{"TABLE_NAME"};
   $temp =~s/gcov_failure_reasons_//g;
   if(!($temp =~m/temp/)) {
    push(@builds1,$temp);
   }
 }
 @builds= @builds1;
 #print $builds[0];
 #print Dumper(\@builds);

if($build eq "" ) { $build=$builds[0] ;}
if($more_or_less eq "" ) { $more_or_less ="less"; } 
if($bucket_or_owner eq "") { $bucket_or_owner = "Bucket_view"; }

($build_ver=$build) =~ s/^(\d\d)_(\d).*$/$1$2/g; #To get 191 from 19_10_b006_1_Feb_07
($build_abc =$build) =~s/^(\d\d)_(\d\d)_(.*)$/$1.$2-$3/g; # To get 19.10-b006_1_Feb_07
#################################################################################
my @all_reasons = ('MODEL_LOAD_FAIL','NOT RUN','Running','Interrupted','MSGSUM_NOT_FOUND','LICENSE_ERROR','CORE',' E ','E TFW-943 ADD','STATUS_CHANGE_GREATER_THAN_5','Profiling Error','No space left on device','No rule to make target','Input Source Missing','STATUS_DIFF');
my @all_reasons1 = ('MODEL_LOAD_FAIL','NOT RUN','Running','Interrupted','MSGSUM_NOT_FOUND','LICENSE_ERROR','CORE','ERROR','DEVPASSWD expiry','EXIT status diff > 5','Profiling Error','No space left','No rule to make target','Input Source Missing','STATUS DIFF');
my @bucket_names = ("sanity","flow","customer","eta","ett","misc","model","pcrs","diagnostics","lowpower","rnd","debug_all","raks","gui","license_testing");
my @bucket_names1 = ("Sanity","Flow","Customer","ETA","ETT","Tiger","Misc","Model","PCRS","Diagnostics","Lowpower","RND","Debug_all","RAKS","GUI","License");

my %bucket_names2;
my %bucket_owners = ();
for ($i=0;$i<=$#bucket_names;$i++) {
   $bucket_names2{$bucket_names[$i]} = $bucket_names1[$i];
   ($owner,$reviewer) = getGcovOwnerAndReviewer($bucket_names[$i]);
   $bucket_owners{$bucket_names[$i]} = $owner;
}


#####################MISC FUNCTIONS###############################################################
#sub uniq {
#    my %seen;
#        grep !$seen{$_}++, @_;
# }
#####################Get inputs from webpage#######################################################
#### Read in text from webpage
my $table = "gcov_failure_reasons_"."$build";

my $dbh = getDBH();
my $sth;


sub get_count_from_query {
    $query_this = $_[0];
    my @temp = ();
    my $count = 0;
    $sth = $dbh->prepare("$query_this");
    $sth->execute() or die $DBI::errstr;
    while (my $row = $sth->fetchrow_hashref()) {
          push(@temp,$row); 
    }
    $count = $#temp + 1;
    return($count);
    
}
sub getLineCount {
    my $filename = $_[0];
    if(-e "$filename") {
      my $result = `wc -l $filename`;
      ($count,$tcName) = split(" ",$result);
      return($count);
    }
  return(0);
}

#print "<br>$query<br>";  
      $query_done = "SELECT * from $table where TC_NAME!=''" ;  #To get %Done
  if ($reason eq "" && $command eq "" ) {
      $query = "SELECT * from $table where reason != ''" ;
   }
   elsif($reason ne "" && $command eq "") {
    if($reason eq " E ") {
      $query = "SELECT * from $table where (reason regexp 'E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%')";
    } else {  
         $query = "SELECT * from $table where reason like '%$reason%'";
      }
   }
   elsif ($reason eq "" && $command ne "" ) {
    $query = "SELECT * from $table where command like '%$command%'";
   }
   else {
       if($reason eq " E ") {
           $query = "SELECT * from $table where reason regexp 'E [[:alnum:]]+'  AND command like '%$command%'";
       } else {
            $query = "SELECT * from $table where (reason like '%$reason%' AND command like '%$command%')";
       }
   }
 if($bucket ne "" ) {
    if($bucket ne "license_testing" && $bucket ne "misc") {
    $query .= "AND TC_NAME like '%/etautotest/$bucket%'";
    $query_done .= " AND TC_NAME like '%/etautotest/$bucket%'";
    }
    elsif ($bucket eq "license_testing") {
    $query .= "AND TC_NAME like '%/etautotest/misc/%License_Testing%'";
    $query_done .= " AND TC_NAME like '%/etautotest/misc/%License_Testing%'";
    }
    else {
     $query .= "AND TC_NAME like '%/etautotest/misc%' AND TC_NAME not like '%/etautotest/misc/%License_Testing%'";
     $query_done .= "AND TC_NAME like '%/etautotest/misc%' AND TC_NAME not like '%/etautotest/misc/%License_Testing%'";
    }

 }  
#$analysis_done_count = 0;
#$analysis_pending_count = 0;
#$analysis_others_count = 0;
  $my_query1 = $query." AND analysis = 'pending'";
  $my_query11 = $query." AND analysis = 'pending' and (reason not like '%NOT RUN%' and reason not like '%Running%' and reason not like '%Interrupted%')";
  $my_query12 = $query." AND analysis = 'pending' and (reason like '%NOT RUN%' or reason like '%Running%' or reason like '%Interrupted%')";
  $my_query2 = $query_done." AND analysis like '%done%'";

  $my_query3 = $query_done." AND ccr REGEXP '^(CCR|CCMPR)*[0-9]+\$'";
  $my_query4 = $query." AND ( analysis != 'pending' and analysis not like '%done%' AND ccr NOT REGEXP '^(CCR|CCMPR)*[0-9]+\$')";
 


#print "$my_query12<br>";
if($analysis_status ne "" ) {
   
   if($analysis_status eq "Pending_Analysis") {
      $query .= " AND analysis = 'pending' and (reason not like '%NOT RUN%' and reason not like '%Running%' and reason not like '%Interrupted%')";  
   }
   elsif($analysis_status eq "Pending_Run") {
      $query .= " AND analysis = 'pending' and (reason like '%NOT RUN%' or reason like '%Running%' or reason like '%Interrupted%')";
    }
   elsif($analysis_status eq "Done") {
      $query = $query_done." AND analysis like '%done%'";
   }
   elsif($analysis_status eq "CCR") {
       $query .= " AND ccr REGEXP '^(CCR|CCMPR)*[0-9]+\$'";
   }
   else {
      $query .= " AND ( analysis != 'pending' and analysis not like '%done%' AND ccr NOT REGEXP '^(CCR|CCMPR)*[0-9]+\$')";
   } 

}
#print "$query<br>";
  $analysis_pending_count_analysis = &get_count_from_query("$my_query11");
  $analysis_pending_count_run = &get_count_from_query("$my_query12");
  $analysis_pending_count = &get_count_from_query("$my_query1");
  $analysis_done_count = &get_count_from_query("$my_query2");
  $analysis_ccr_count = &get_count_from_query("$my_query3");
  $analysis_others_count = &get_count_from_query("$my_query4");

#print "$my_query1 <br>$my_query2 <br>$my_query3 <br>$my_query4<br>";
#print" p=$analysis_pending_count d=$analysis_done_count c=$analysis_ccr_count o=$analysis_others_count <br>";
  $total_analysis_count = $analysis_pending_count + $analysis_done_count + $analysis_ccr_count + $analysis_others_count; 
$sth = $dbh->prepare("$query");
$sth->execute() or die $DBI::errstr;
#print"$query<br>";
my @data;
while (my $row = $sth->fetchrow_hashref()) {
    my $data = $row->{TC_NAME} . "::::" . $row->{REASON} . "::::" . $row->{command} . "::::" .$row->{CCR} ."::::" . $row->{msgidstatus};
    push(@data,$data);
}
my @command_options = () ;
       if($reason eq " E ") {
            $query_for_command = "SELECT DISTINCT command from $table where REASON regexp 'E [[:alnum:]]+'";
        } else {
            $query_for_command="SELECT DISTINCT command from $table where REASON like '%$reason%'" ;
        }
       #print"$query_for_command<br>";
       $sth = $dbh->prepare("$query_for_command");
       $sth->execute() or die $DBI::errstr;
   while (my $row = $sth->fetchrow_hashref()) {
      my $data1 = $row->{command};
      $data1=~ s/^\s+|\s+$//g; # Trim whitespace
      push(@data1,$data1);
    } 
 
     # @data1 = split("\n",$data1);
      #print Dumper (\@data1);
      foreach(@data1){
        if( ( defined $_) and !($_ =~ /^$/ )){   # to ignore empty elements
            my %params = map { $_ => 1 } @all_commands;   # to ignore garbage values as command
            if(exists($params{$_})) {
              push(@command_options, $_);
            }
        }
      }
my @command_options1 = uniq(sort @command_options); 
#print Dumper (\@all_commands);
#print Dumper (\@command_options1);
my @ccrs=();
      
       if($reason eq " E ") {
            $query_for_ccr="SELECT DISTINCT CCR from $table where (REASON regexp 'E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') and command = '$command'";
        } else {
           $query_for_ccr="SELECT DISTINCT CCR from $table where REASON like '%$reason%' and command = '$command'";
        }
          #print"$query_for_ccr<br>";
           $sth=$dbh->prepare("$query_for_ccr");
           $sth->execute() or die $DBI::errstr;
   while (my $row = $sth->fetchrow_hashref()) {
         my $data1 = $row->{CCR};
         push(@ccrs,$data1);
   }
#print Dumper(\@ccrs);
my %command_count;
my %reason_count;
my %allfailures_count;
my %pending_count;
my %pending_run_count;
my %pending_analysis_count;
my %done_count;
my %ccr_count;
my %pending_percentage;

#######################Code for getting Count All Failures and Pending Bucketswise###########################
foreach $mybucket (@bucket_names) {
  %total_testcases;
  %total_testcases_count;
  my $bucket_name = $mybucket;
   my $query1,$query2;
   if ($mybucket ne "license_testing" && $mybucket ne "misc") {
     $query1 = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/$mybucket%'";
     $query2 = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/$mybucket%' and analysis='pending'";
     $query3 = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/$mybucket%' and analysis='pending' and (REASON like '%NOT RUN%' OR REASON like 'Running' OR REASON like 'Interrupted')";
      $query4 = "SELECT DISTINCT COUNT(TC_NAME) from $table where TC_NAME like '%/etautotest/$mybucket%' "; #For Total
     $query5 = "SELECT DISTINCT COUNT(TC_NAME) from $table where TC_NAME like '%/etautotest/$mybucket%' AND REASON = ''"; #For Done

   }
   elsif ($mybucket eq "license_testing") {
     $query1 = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/misc/%License_Testing%'";
     $query2 = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/misc/%License_Testing%' and analysis='pending'";
     $query3 = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/misc/%License_Testing%' and analysis='pending' and (REASON like '%NOT RUN%' OR REASON like 'Running' OR REASON like 'Interrupted')";
      $query4 = "SELECT DISTINCT COUNT(TC_NAME) from $table where TC_NAME like '%/etautotest/misc/%License_Testing%'";
     $query5 = "SELECT DISTINCT COUNT(TC_NAME) from $table where TC_NAME like '%/etautotest/misc/%License_Testing%' AND REASON = ''";

   }
   else {
       $query1 = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/misc/%'  AND TC_NAME not like '%/etautotest/misc/%License_Testing%'";
       $query2 = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/misc/%'  AND TC_NAME not like '%/etautotest/misc/%License_Testing%' and analysis='pending'";
       $query3 = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/misc/%'  AND TC_NAME not like '%/etautotest/misc/%License_Testing%' and analysis='pending' and (REASON like '%NOT RUN%' OR REASON like 'Running' OR REASON like 'Interrupted')";
         $query4 = "SELECT DISTINCT COUNT(TC_NAME) from $table where TC_NAME like '%/etautotest/misc/%'  AND TC_NAME not like '%/etautotest/misc/%License_Testing%'";
       $query5 = "SELECT DISTINCT COUNT(TC_NAME) from $table where TC_NAME like '%/etautotest/misc/%'  AND TC_NAME not like '%/etautotest/misc/%License_Testing%' AND REASON = ''";

   }
   my @all_failures_count = $dbh->selectrow_array($query1);
   $allfailures_count{$mybucket} =  @all_failures_count[0];
   my @pending1_count = $dbh->selectrow_array($query2); 
    $pending_count{$mybucket} = @pending1_count[0];
   my @pending_run_count =  $dbh->selectrow_array($query3);
     $pending_run_count{$mybucket} = @pending_run_count[0];
     $pending_analysis_count{$mybucket} = @pending1_count[0] - @pending_run_count[0] ;

      my @done_testcases_count = $dbh->selectrow_array($query5);
     $done_count{$mybucket} = @done_testcases_count[0];

      my @total_testcases_count = $dbh->selectrow_array($query4);
     $total_testcases_count{$bucket_name} = @total_testcases_count[0];

      my @total_testcases_count_all = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table");  
     $total_testcases_count{'total'}= @total_testcases_count_all[0];


    if($allfailures_count{$mybucket} != 0 ) {
	if($total_testcases_count{$mybucket} != 0 ) {
        #print"$mybucket $pending_count{$mybucket} $total_testcases_count{$mybucket} <br>";
        my $percentage2 = ($pending_count{$mybucket}/$total_testcases_count{$mybucket}) * 100 ;
        $pending_percentage{$mybucket} = sprintf "%.1f",$percentage2;
	#print "$percentage2";
	}
	#print "$mybucket  $pending_count{$mybucket}  $total_testcases_count{$mybucket} $percentage2<br>";
   }
}
#print Dumper(\%allfailures_count);
#print Dumper (\%total_testcases_count);
#print Dumper(\%pending_count);
#print Dumper(\%pending_percentage);
#print Dumper(\%pending_count);
#print Dumper(\%done_count);
###########################################################################################################
foreach $bkt (@bucket_names){
  foreach $reason (@all_reasons) {
    my @temp;
    my @temp1;  ### Without CCR
      my @temp2;  #### With CCR
      my $i =0 ;
    if($reason eq " E ") {
      if($bkt ne "license_testing" && $bkt ne "misc") {
	@temp = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%' AND reason not like '%No rule to make target%'  AND reason not like '%Input Source missing%') AND TC_NAME like '%/etautotest/$bkt%'");
	@temp1 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%' AND reason not like '%No rule to make target%'  AND reason not like '%Input Source missing%' ) AND TC_NAME like '%/etautotest/$bkt%' and CCR='NA'");
	@temp2 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%' AND reason not like '%No rule to make target%'  AND reason not like '%Input Source missing%' ) AND TC_NAME like '%/etautotest/$bkt%' and CCR!='NA'");
      }
      elsif ($bkt eq "license_testing") {
	@temp = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/misc/%License_Testing%'");
	@temp1 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/misc/%License_Testing%' and CCR='NA'");
	@temp2 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/misc/%License_Testing%' and CCR!='NA'");
      }
      else {
	@temp = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%' AND reason not like '%No rule to make target%'  AND reason not like '%Input Source missing%' ) AND TC_NAME like '%/etautotest/misc%' and TC_NAME not like '%/etautotest/misc/%License_Testing%'");
	@temp1 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/misc%' and TC_NAME not like '%/etautotest/misc/%License_Testing%' and CCR='NA'");
	@temp2 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/misc%' and TC_NAME not like '%/etautotest/misc/%License_Testing%' and CCR!='NA'");
      }
    }
    else {
      if($bkt ne "license_testing" && $bkt ne "misc") {
	@temp = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/$bkt%'");
	@temp1 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/$bkt%' and CCR='NA'");
	@temp2 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/$bkt%' and CCR!='NA'");
      }
      elsif ($bkt eq "license_testing") {
	@temp = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/misc/%License_Testing%'");
	@temp1 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/misc/%License_Testing%' and CCR='NA'");
	@temp2 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/misc/%License_Testing%' and CCR!='NA'");
      }
      else {
	@temp = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/misc%' and TC_NAME  not like '%/etautotest/misc/%License_Testing%'");
	@temp1 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/misc%' and TC_NAME  not like '%/etautotest/misc/%License_Testing%' and CCR='NA'");
	@temp2 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/misc%' and TC_NAME  not like '%/etautotest/misc/%License_Testing%' and CCR!='NA'");
      }
    }
    $reason_count_bkt{$bkt}{$reason} = $temp[0] ;
    $reason_count_noccr_bkt{$bkt}{$reason} = $temp1[0] ;
    $reason_count_ccr_bkt{$bkt}{$reason} = $temp2[0] ;
  }

}
##### NEW CODE FOR OWNER VIEW ###
### To get unique owners ###
@owners=uniq values %bucket_owners;
my %owners_bucket=(); ## Maps owners with buckets
my %reason_count_noccr_owner=(); ## Maps issues count on owner level
my %pending_analysis_count_owner;
my %pending_run_count_owner;
my %allfailures_count_owner = ();
my %total_testcases_count_owner = ();
my %pending_percentage_owner =();
my %pending_count_owner =();

foreach my $owner (@owners) {
    foreach my $bucket (keys %bucket_owners) {
     if ($owner eq $bucket_owners{$bucket}) {
       $owners_bucket{$owner} .= $bucket . "," ;
         foreach $reason (@all_reasons) {
             $reason_count_noccr_owner{$owner}{$reason} +=  $reason_count_noccr_bkt{$bucket}{$reason} ; ### To get similar data at owner level
	 }    
	     $pending_analysis_count_owner{$owner} += $pending_analysis_count{$bucket};
	     $pending_run_count_owner{$owner} += $pending_run_count{$bucket};
	     $allfailures_count_owner{$owner} += $allfailures_count{$bucket};
	     $total_testcases_count_owner{$owner} += $total_testcases_count{$bucket};

	     $pending_count_owner{$owner} = $pending_analysis_count_owner{$owner} +  $pending_run_count_owner{$owner};
	     if ($total_testcases_count_owner{$owner} != 0) {
	      my $percentage2 = ($pending_count_owner{$owner}/$total_testcases_count_owner{$owner}) * 100 ;
              $pending_percentage_owner{$owner} = sprintf "%.1f",$percentage2;
	     }

     }
     else {
         next; 
     }
   }
  $owners_bucket{$owner} =~ s/,$//g ;
}
############################################################################################################
foreach $reason (@all_reasons) {
     my @temp;
     my @temp1;  ### Without CCR
     my @temp2;  #### With CCR
     my $i =0 ; 
     if($reason eq " E ") {
       if($bucket ne "license_testing" && $bucket ne "misc") {
       @temp = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/$bucket%'");
       @temp1 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/$bucket%' and CCR='NA'");
       @temp2 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/$bucket%' and CCR!='NA'");
        }
        elsif ($bucket eq "license_testing") {
        @temp = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/misc/%License_Testing%'");
        @temp1 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/misc/%License_Testing%' and CCR='NA'");
        @temp2 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/misc/%License_Testing%' and CCR!='NA'");
        }
        else {
         @temp = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/misc%' and TC_NAME not like '%/etautotest/misc/%License_Testing%'");
         @temp1 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/misc%' and TC_NAME not like '%/etautotest/misc/%License_Testing%' and CCR='NA'");
         @temp2 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where (REASON regexp ' E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') AND TC_NAME like '%/etautotest/misc%' and TC_NAME not like '%/etautotest/misc/%License_Testing%' and CCR!='NA'");
         }
     }
     else {
        if($bucket ne "license_testing" && $bucket ne "misc") {
         @temp = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/$bucket%'");
         @temp1 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/$bucket%' and CCR='NA'");
         @temp2 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/$bucket%' and CCR!='NA'");
         }
         elsif ($bucket eq "license_testing") {
          @temp = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/misc/%License_Testing%'");
          @temp1 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/misc/%License_Testing%' and CCR='NA'");
          @temp2 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/misc/%License_Testing%' and CCR!='NA'");
          }
         else {
           @temp = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/misc%' and TC_NAME  not like '%/etautotest/misc/%License_Testing%'");
           @temp1 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/misc%' and TC_NAME  not like '%/etautotest/misc/%License_Testing%' and CCR='NA'");
           @temp2 = $dbh->selectrow_array("SELECT DISTINCT COUNT(TC_NAME) from $table where REASON like '%$reason%' AND TC_NAME like '%/etautotest/misc%' and TC_NAME  not like '%/etautotest/misc/%License_Testing%' and CCR!='NA'");
         }
     }
      $reason_count{$reason} = $temp[0] ;
      $reason_count_noccr{$reason} = $temp1[0] ;
      $reason_count_ccr{$reason} = $temp2[0] ;
}
      my $all_failures_count_query;
      my $all_failures_count_query_noccr;
      my $all_failures_count_query_ccr;
       if($bucket ne "license_testing" && $bucket ne "misc") {
         $all_failures_count_query = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/$bucket%'";
         $all_failures_count_query_noccr = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/$bucket%' and CCR='NA'";
         $all_failures_count_query_ccr = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/$bucket%' and CCR!='NA'";
        }
        elsif($bucket eq "license_testing") { 
           $all_failures_count_query = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/misc/%License_Testing%'";
           $all_failures_count_query_noccr = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/misc/%License_Testing%' and CCR='NA'";
           $all_failures_count_query_ccr = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/misc/%License_Testing%' and CCR!='NA'";
         }
         else {
           $all_failures_count_query = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/misc%' and TC_NAME not like '%/etautotest/misc/%License_Testing%'" ;
           $all_failures_count_query_noccr = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/misc%' and TC_NAME not like '%/etautotest/misc/%License_Testing%' and CCR='NA'" ;
           $all_failures_count_query_ccr = "SELECT DISTINCT COUNT(TC_NAME) from $table where REASON != '' AND TC_NAME like '%/etautotest/misc%' and TC_NAME not like '%/etautotest/misc/%License_Testing%' and CCR!='NA'" ;
          }
      my @all_failures_count = $dbh->selectrow_array("$all_failures_count_query");
      my @all_failures_count_noccr = $dbh->selectrow_array("$all_failures_count_query_noccr");
      my @all_failures_count_ccr = $dbh->selectrow_array("$all_failures_count_query_ccr");
      $reason_count{"all_failures"}= @all_failures_count[0];
      $reason_count{"all_failures_noccr"}= @all_failures_count_noccr[0];
      $reason_count{"all_failures_ccr"}= @all_failures_count_ccr[0];


foreach $command (@command_options1) {
      my @temp;
      if($reason eq "") {
          my $query1;
          if($bucket ne "license_testing" && $bucket ne "misc") {
              $query1 = "SELECT DISTINCT COUNT(TC_NAME) from $table where command like '% $command%' AND TC_NAME like '%/etautotest/$bucket%'";
          }
          elsif ($bucket eq  "license_testing") {
                $query1 = "SELECT DISTINCT COUNT(TC_NAME) from $table where command like '% $command%' AND TC_NAME like '%/etautotest/misc/%License_Testing%'";
          }
          else {
               $query1 = "SELECT DISTINCT COUNT(TC_NAME) from $table where command like '% $command%' AND TC_NAME like '%/etautotest/misc%' and TC_NAME not like '%/etautotest/misc/%License_Testing%'" ;
          }
            
          @temp = $dbh->selectrow_array("$query1");
         $command_count{$command} = $temp[0];
      }else {
             my $query2;
             if($bucket ne "license_testing" && $bucket ne "misc") {
               $query2 = "SELECT DISTINCT COUNT(TC_NAME) from $table where ((reason regexp 'E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') and command like '% $command%') AND TC_NAME like '%/etautotest/$bucket%'";
              }
              elsif ($bucket eq  "license_testing") {
                $query2 = "SELECT DISTINCT COUNT(TC_NAME) from $table where ((reason regexp 'E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') and command like '% $command%') AND TC_NAME like '%/etautotest/misc/%License_Testing%'";
                }
               else {
                $query2 = "SELECT DISTINCT COUNT(TC_NAME) from $table where ((reason regexp 'E [[:alnum:]]+' AND reason not like '%CORE%' AND reason not like '%STATUS_DIFF%') and command like '% $command%') AND TC_NAME like '%/etautotest/misc%' and TC_NAME not like '%/etautotest/misc/%License_Testing%'" ;
               } 
              if($reason eq " E ") {
                 @temp = $dbh->selectrow_array("$query2");
               }
              else {
                 my $query3= "SELECT DISTINCT COUNT(TC_NAME) from $table where (reason like '%$reason%' and command like '% $command%') AND TC_NAME like";
                 if($bucket ne "license_testing" && $bucket ne "misc") {
                  $query3 .= "'%/etautotest/$bucket%'";
                 }
                 elsif ($bucket eq  "license_testing") {
                   $query3 .= "'%/etautotest/misc/%License_Testing%'";
                  }
                 else {
                    $query3 .= "'%/etautotest/misc%' and TC_NAME not like '%/etautotest/misc/%License_Testing%'";
                 }
	 #print "$query3 <br>";	 
          @temp = $dbh->selectrow_array("$query3");
              }
         $command_count{$command} = $temp[0];
       }
} 
  my $msgidstatus_not_found_count = get_count_from_query("SELECT tc_name from $table where msgidstatus = 'NOT FOUND' AND REASON = ''");

#print"SELECT tc_name from $table where msgidstatus = 'NOT FOUND' AND REASON = '' ::: $msgidstatus_not_found_count <br>";
#print "Hey  $msgidstatus_not_found_count<br>";
  

#print Dumper(\@command_options1);
#print Dumper(\%command_count);
#print Dumper(\%reason_count);
# $var= categorizeFromIgnoreFile("/lan/fed/etpv/cgi-bin/gcov_failure_reasons/IGNORE_TCS");
#categorizeFromIgnoreFile("/lan/fed/etpv/cgi-bin/gcov_failure_reasons/IGNORE_TCS"); // now called in remove_temp_links.pl which is called with cron run.csh
################################################################################################

print "<html>";
print "<head>\n";
print "<meta charset='UTF-8'>";
print "<title>GCOV Failures</title>";
print "<link href='http://etpv/lan/fed/etpv/cgi-bin/status_tracker/css/w3.css' rel='stylesheet'>";

print <<END;
<script src="http://etpv/lan/fed/etpv/benchscript/Scripts/jquery-1.7.1.min.js"></script>
<script src="http://etpv/lan/fed/etpv/benchscript/Scripts/jquery-ui-1.8.20.js"></script>
<link rel="Stylesheet" href="/lan/fed/etpv/cgi-bin/jquery_table_nishant.css" />
<script type="text/javascript" src="/lan/fed/etpv/cgi-bin/datatable_nishant.js"></script>

<style>
.simple_table tr,td,th {
    border: 1px solid black;
}
#form_box {
    width: 90%;
    padding: 20px;
    border: 3px solid gray;
    margin: 20px;
    overflow: hidden;
    white-space: nowrap;
}
.vertical-text {
     writing-mode: vertical-rl;
        transform: rotate(-180deg);
}

.vertical-text span {
      text-orientation: upright;
}

</style>
<script>
  \$(document).ready( function () {
     var table2 = \$('#example2').dataTable({
          orderCellsTop: true,
           pageLength: -1,
          fixedHeader: true,
          autoWidth: false
     }); 
      var table = \$('#example').dataTable({
          "lengthMenu": [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
           pageLength: -1,
          "bAutoWidth": false, // Disable the auto width calculation
          "sSearch": "Search all columns:"
     });
  } );

</script>

END
print "</head>";

print "<body>";
#print join (" ",@command_options1);
#print "$var Preeti<br>";
print "<div class='w3-card w3-round w3-lime'><h1><center><b>GCOV Failure Analysis</b></center></h1></div>";
print"<div style='float:right;font-size:15px;'>";
print "<p >This Webpage is Updated every 3 hours";
print "<br>Last Updated on $timestamp.</p>";
print"</div>";
print"<br>";
print"<div id='form_box'>";
#print "$query<br>";
print "<form action='' method='GET' target='_self' id='myform' name='myform' style='font-size:15px'>";
print"<label><b>Build : </label></b>";
print"<select name='build' id='build' onchange=document.getElementById(\"myform\").submit();>";
for($i=0;$i<=$#builds; $i++) {
    if($build eq $builds[$i]) {
       print "<option value='$builds[$i]' selected>$builds[$i]</option>";
    }  
    else { print "<option value='$builds[$i]'>$builds[$i]</option>"; }
}
print"</select>";
print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp";
print"<label><b>Bucket : </label></b>";
print"<select name='bucket' id='bucket' onchange=document.getElementById(\"myform\").submit();>";
print "<option value=''>ALL</option>";
for($i=0;$i<=$#bucket_names; $i++) {

    ($bucket_owner,$bucket_reviewer) = getGcovOwnerAndReviewer($bucket_names[$i]); 
   if($allfailures_count{$bucket_names[$i]} !=  0 ) {
       #my $percentage2 = ($pending_count{$bucket_names[$i]}/$allfailures_count{$bucket_names[$i]}) *100;
    my $percentage2 = ($pending_count{$bucket_names[$i]}/$total_testcases_count{$bucket_names[$i]}) *100;
    my $percentage = sprintf "%.1f",$percentage2;
  # print "$bucket_names[$i] ::: $pending_percentage{$bucket_names[$i]} <br>";
    if($bucket eq $bucket_names[$i]) {
       print "<option value='$bucket_names[$i]' selected>$bucket_names1[$i]   ($bucket_owner)&nbsp&nbsp $pending_count{$bucket_names[$i]}/$total_testcases_count{$bucket_names[$i]} ($percentage %) </option>";
    }  
    else { print "<option value='$bucket_names[$i]'>$bucket_names1[$i]   ($bucket_owner)&nbsp&nbsp $pending_count{$bucket_names[$i]}/$total_testcases_count{$bucket_names[$i]} ($percentage %) </option>"; 
    }
    }
}
print"</select>";
print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp";
print "<br><br><label><b>Failure Reason :  </label></b>";
print "<select name='reason' id='reason' onchange=document.getElementById(\"myform\").submit();>";
print "<option value='' >ALL FAILURES($reason_count{all_failures})</option>";
for($i=0;$i<=$#all_reasons; $i++) {
   if($reason eq $all_reasons[$i]) {
      print"<option value='$all_reasons[$i]' selected>$all_reasons1[$i]  ($reason_count{$all_reasons[$i]})</option>";
   }
   else {
   print"<option value='$all_reasons[$i]'>$all_reasons1[$i]  ($reason_count{$all_reasons[$i]})</option>";
   }
}
print "</select>";
print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp";
print "<label><b>Command : </label></b>";
print "<select name='command' id='command' onchange=document.getElementById(\"myform\").submit();>";
 if($command eq "" ) {
 print "<option value='' selected  >ALL COMMANDS</option>";
 }
 else {
 print "<option value='' >ALL COMMANDS</option>";
 }
 for($i=0;$i<=$#command_options1;$i++) {
   if($command_count{$command_options1[$i]} !=0 ) {
    if($command eq $command_options1[$i]) {
       print"<option value='$command_options1[$i]' selected>$command_options1[$i]  ($command_count{$command_options1[$i]})</option>";
    }
    else {
       print"<option value='$command_options1[$i]'>$command_options1[$i]  ($command_count{$command_options1[$i]})</option>";
    }
   }
  }
print"</select>";
@analysis_status1 = ("Pending Analysis","Pending Run","Done","CCR","Others/Comments");
@analysis_status = ("Pending_Analysis","Pending_Run","Done","CCR","Others/Comments");
@analysis_count =("$analysis_pending_count_analysis","$analysis_pending_count_run","$analysis_done_count","$analysis_ccr_count","$analysis_others_count");
print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp";
print "<label><b>Analysis : </label></b>";

print "<select name='analysis_status' id='analysis_status' onchange=document.getElementById(\"myform\").submit();>";
  if($analysis_status eq "" ) {
    print "<option value='' selected  >SELECT</option>";
  }
  else {
    print "<option value=''>SELECT</option>";
  }
 # print "Hey $total_analysis_count <br>";
 for($i=0;$i<=$#analysis_status;$i++) {
     my $percentage1 = ($analysis_count[$i]/$total_analysis_count) *100; 
     my $percentage = sprintf "%.1f",$percentage1;
     #print"$percentage :: $analysis_status[$i]" ;
     if($analysis_status eq $analysis_status[$i]) {
        print"<option value='$analysis_status[$i]' selected >$analysis_status1[$i] ($analysis_count[$i]) [ $percentage %]</option>";
      }
     else {
         print"<option value='$analysis_status[$i]'>$analysis_status1[$i] ($analysis_count[$i]) [ $percentage %]</option>";
     }
  }
print"</select>";
print"<input type='hidden' id='more_or_less' name='more_or_less' value=''>";
print"<input type='hidden' id='bucket_or_owner' name='bucket_or_owner' value=''>";

print "</form>";
print"</div>";

#print "<input type='submit' value='Submit' class='w3-btn w3-small w3-blue '>";
my $count_tc = $#data +1 ;
print"<table  ><tr>";
print"<td>";

if($bucket_or_owner eq "Bucket_view") {
  print "<input type='button' id='button_value1' value='Owner_view' form='myform' onclick=my_function2()>";
}
else {
  print "<input type='button' id='button_value1' value='Bucket_view' form='myform' onclick=my_function2()>";
}

print"<table id='example2' style='border-collapse:collapse;width:20%' class='simple_table' >\n";  #Table for Owner wise status
print"<thead>";
if($bucket_or_owner eq "Bucket_view") {
   print"<tr><td>S.no</td><td>Bucket</td><td>Owner</td>";
}
else {
   print"<tr><td>S.no</td><td>Owner</td><td>Buckets</td>";
} 


print"<td><p class='vertical-text'>MODEL_LOAD_FAIL</p></td>
<td><p class='vertical-text'>CORE</p></td>
<td><p class='vertical-text'>ERROR</p></td>
<td><p class='vertical-text'>EXIT status diff >5</p></td>
<td><p class='vertical-text'>DEVPASSWD expiry</p></td>
<td><p class='vertical-text'>Profiling Error</p></td>
<td><p class='vertical-text'>No space left</p></td>
<td colspan=2>Pending</td><td>Total<br>Pending</td><td>Total<br>Testcases</td><td>% Pending</td></tr>";
print"<tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>Analysis</td><td>Run</td><td><td></td><td>% Pending</td></tr>";
print"</thead>";
my $num = 1;
$pending_analysis_count{'total'}=0;
$pending_run_count{'total'}=0;
$allfailures_count{'total'}=0;

if($bucket_or_owner eq "Bucket_view") {
  foreach $bucket_name (sort {$bucket_owners{$a} cmp $bucket_owners{$b}} keys %bucket_owners ) {
   # my $bucket_name = grep {$bucket_owners{$_} eq $owner } keys %bucket_owners ;
   print"<tr><td>$num</td><td>$bucket_names2{$bucket_name}</td><td>$bucket_owners{$bucket_name}</td>
   <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=MODEL_LOAD_FAIL&rr=MODEL_LOAD_FAIL&ccr=no target='_blank'>$reason_count_noccr_bkt{$bucket_name}{'MODEL_LOAD_FAIL'}</a></td>
    <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=CORE&rr=CORE&ccr=no' target='_blank'>$reason_count_noccr_bkt{$bucket_name}{'CORE'}</a></td>
    <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=%20E%20&rr=ERROR&ccr=no'target='_blank' >$reason_count_noccr_bkt{$bucket_name}{' E '}</a></td>

    <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=STATUS_CHANGE_GREATER_THAN_5&rr=Exit status diff >5&ccr=no' target='_blank'>$reason_count_noccr_bkt{$bucket_name}{'STATUS_CHANGE_GREATER_THAN_5'}</a></td>
    <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=E%20TFW-943%20ADD&rr=E%20TFW-943%20ADD&ccr=no' target='_blank'>$reason_count_noccr_bkt{$bucket_name}{'E TFW-943 ADD'}</a></td>
    <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=Profiling%20Error&rr=Profiling%20Error&ccr=no' target='_blank'>$reason_count_noccr_bkt{$bucket_name}{'Profiling Error'}</a></td>
    <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=No%20space%20left%20on%20device&rr=No%20space%20left%20on%20device&ccr=no' target='_blank'>$reason_count_noccr_bkt{$bucket_name}{'No space left on device'}</a></td>
  ";
  $total{'MODEL_LOAD_FAIL'}+=$reason_count_noccr_bkt{$bucket_name}{'MODEL_LOAD_FAIL'};
  $total{'CORE'}+=$reason_count_noccr_bkt{$bucket_name}{'CORE'};
  $total{' E '}+=$reason_count_noccr_bkt{$bucket_name}{' E '};
  $total{'STATUS_CHANGE_GREATER_THAN_5'}+=$reason_count_noccr_bkt{$bucket_name}{'STATUS_CHANGE_GREATER_THAN_5'};
  $total{'DEVPASSWD expiry'}+=$reason_count_noccr_bkt{$bucket_name}{'DEVPASSWD expiry'};
  $total{'Profiling Error'}+=$reason_count_noccr_bkt{$bucket_name}{'Profiling Error'};
  $total{'No space left on device'}+=$reason_count_noccr_bkt{$bucket_name}{'No space left on device'};

  print "
   <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&analysis_status=Pending_Analysis' target='_blank'>$pending_analysis_count{$bucket_name}</a></td>";
   print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&analysis_status=Pending_Run' target='_blank'>$pending_run_count{$bucket_name}</a></td>";
   print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name' target='_blank'>$allfailures_count{$bucket_name}</a></td>";
   print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&count=all' target='_blank'>$total_testcases_count{$bucket_name}</a></td><td>$pending_percentage{$bucket_name}</td>";
   print"</tr>"; 
  $pending_analysis_count{'total'} = $pending_analysis_count{'total'} + $pending_analysis_count{$bucket_name};
  $pending_run_count{'total'} = $pending_run_count{'total'} + $pending_run_count{$bucket_name} ;
  $allfailures_count{'total'} = $allfailures_count{'total'} + $allfailures_count{$bucket_name};

  $num++;
  }
}
else {
  foreach $owner (sort keys %owners_bucket ) {
      print"<tr><td>$num</td><td>$owner</td><td>$owners_bucket{$owner}</td>";
      my $bucket_name = $owners_bucket{$owner};
 print"
 <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=EXIT%20STATUS%201&rr=EXIT%20STATUS%201&ccr=no target='_blank'>$reason_count_noccr_owner{$owner}{'MODEL_LOAD_FAIL'}</a></td>
  <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=CORE&rr=CORE&ccr=no' target='_blank'>$reason_count_noccr_owner{$owner}{'CORE'}</a></td>
  <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=%20E%20&rr=ERROR&ccr=no'target='_blank' >$reason_count_noccr_owner{$owner}{' E '}</a></td>

  <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=STATUS_CHANGE_GREATER_THAN_5&rr=Exit status diff >5&ccr=no' target='_blank'>$reason_count_noccr_owner{$owner}{'STATUS_CHANGE_GREATER_THAN_5'}</a></td>
    <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=E%20TFW-943%20ADD&rr=E%20TFW-943%20ADD&ccr=no' target='_blank'>$reason_count_noccr_owner{$owner}{'E TFW-943 ADD'}</a></td>
    <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=Profiling%20Error&rr=Profiling%20Error&ccr=no' target='_blank'>$reason_count_noccr_owner{$owner}{'Profiling Error'}</a></td>
    <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=No%20space%20left%20on%20device&rr=No%20space%20left%20on%20device&ccr=no' target='_blank'>$reason_count_noccr_owner{$owner}{'No space left on device'}</a></td>
";
$total{'MODEL_LOAD_FAIL'}+=$reason_count_noccr_owner{$owner}{'MODEL_LOAD_FAIL'};
$total{'CORE'}+=$reason_count_noccr_owner{$owner}{'CORE'};
$total{' E '}+=$reason_count_noccr_owner{$owner}{' E '};
$total{'STATUS_CHANGE_GREATER_THAN_5'}+=$reason_count_noccr_owner{$owner}{'STATUS_CHANGE_GREATER_THAN_5'};
$total{'DEVPASSWD expiry'}+=$reason_count_noccr_owner{$owner}{'E TFW-943 ADD'};
$total{'Profiling Error'}+=$reason_count_noccr_owner{$owner}{'Profiling Error'};
$total{'No space left on device'}+=$reason_count_noccr_owner{$owner}{'No space left on device'};
print "
 <td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&analysis_status=Pending_Analysis' target='_blank'>$pending_analysis_count_owner{$owner}</a></td>";
 print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&analysis_status=Pending_Run' target='_blank'>$pending_run_count_owner{$owner}</a></td>";
 print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name' target='_blank'>$allfailures_count_owner{$owner}</a></td>";
 print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&count=all' target='_blank'>$total_testcases_count_owner{$owner}</a></td>";
 print"<td>$pending_percentage_owner{$owner}</td></tr>"; 
$pending_analysis_count_owner{'total'} = $pending_analysis_count_owner{'total'} + $pending_analysis_count_owner{$owner};
$pending_run_count_owner{'total'} = $pending_run_count_owner{'total'} + $pending_run_count_owner{$owner} ;
$allfailures_count_owner{'total'} = $allfailures_count_owner{'total'} + $allfailures_count_owner{$owner};

     $num++;

 }
}
print "<tfoot>";
print "<tr style='text-align:left;'><td></td><td>Total</td><td></td>";
print"<td style='text-align:left;'><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=&reason=MODEL_LOAD_FAIL&rr=MODEL_LOAD_FAIL&ccr=no' target='_blank'>$total{'MODEL_LOAD_FAIL'}</a></td>";
print"<td style='text-align:left;'><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=&reason=CORE&ccr=no&rr=CORE' target='_blank'>$total{'CORE'}</td></a>";
print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket_name&reason=%20E%20&rr=ERROR&ccr=no' target='_blank' >$total{' E '}</td></a>";
print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=&reason=STATUS_CHANGE_GREATER_THAN_5&ccr=no&rr=Exit status diff >5' target='_blank'>$total{'STATUS_CHANGE_GREATER_THAN_5'}</a></td>";
print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=&reason=DEVPASSWD%20expiry&ccr=no&rr=DEVPASSWD%20expiry' target='_blank'>$total{'DEVPASSWD expiry'}</td></a>";
print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=&reason=Profiling%20Error&ccr=no&rr=Profiling%20Error' target='_blank'>$total{'Profiling Error'}</td></a>";
print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=&reason=No%20space%20left%20on%20device&ccr=no&rr=No%20space%20left%20on%20device' target='_blank'>$total{'No space left on device'}</td></a>";


print"<td>$pending_analysis_count{'total'}</td>";
print"<td>$pending_run_count{'total'}</td>";
print "<td>$allfailures_count{'total'} </td>";
print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&count=all' target='_blank'>$total_testcases_count{'total'}</a></td>";
print"<td></td></tr>";
print "</tfoot>";
print "</table>";
print"</td>";
##########################

print"<td>";
print"<table  style='border-collapse:collapse;width:20%' class='simple_table'>\n";  #Table for status
print"<tr><center style='font-size:20px;'><b>Analysis</b></center></tr>";
print"<tr><td>Status</td><td>Count</td><td>Percentage</td></tr>";
 for($i=0;$i<=$#analysis_status;$i++) {
     my $percentage1 = ($analysis_count[$i]/$total_analysis_count) *100; 
     my $percentage = sprintf "%.1f",$percentage1;
     print "<tr><td>$analysis_status1[$i]</td><td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&analysis_status=$analysis_status[$i]&bucket=$bucket&reason=$reason&command=$command' target='_blank'>$analysis_count[$i]</a></td><td>$percentage %</td></tr>";
  }
print"</table>";
############
$count_tc1 = `cat /lan/fed/etpv/cgi-bin/gcov_failure_reasons/rerun_list | wc -l `;
chomp($count_tc1);
print "<br><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket&reason=$reason&command=$command&analysis_status=$analysis_status' target='_blank'>List of Testcases Matching this criteria($count_tc)</a>";
print "<br><a href='/lan/fed/etpv/cgi-bin/gcov_failure_reasons/rerun_list' target='_blank'>List of Testcases to be rerun($count_tc1)</a>";
print "<br><strong>Exceptions</strong><br>";
$count_list_exclude = &getLineCount("list_exclude_sorted");
print"<br><a href='/lan/fed/etpv/cgi-bin/gcov_failure_reasons/list_exclude_sorted' target='_blank'>List Excluded ($count_list_exclude) </a>";
print "&nbsp&nbsp&nbsp&nbsp";
$count_list_ignore = &getLineCount("list_ignore");
print"<br><a href='/lan/fed/etpv/cgi-bin/gcov_failure_reasons/IGNORE_TCS' target='_blank'>List Ignore ($count_list_ignore) </a>";
print "&nbsp&nbsp&nbsp&nbsp";
print"<br><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?msgidstatus=no&build=$build' target='_blank'>Msgidstatus.out not Present ($msgidstatus_not_found_count) </a>";



############
print"</td>";
print"</td><td>&nbsp&nbsp</td>\n";
print"<td>";
  print "<table  style='border-collapse:collapse;width:20%' class='simple_table'>\n"; #Table for command count
   print "<tr><th>S.no</th><th>Top failing Commands</th><th>#Testcases</th></tr>\n";
    $num1=1;
    $total=0;
    foreach $command (reverse sort {$command_count{$a} <=> $command_count{$b}} keys %command_count) {
        $total += $command_count{$command};
        if($command_count{$command} > 0 ) {
        print"<tr><td>$num1</td><td>$command</td><td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket&command=$command' target='_blank'>$command_count{$command}</a></td></tr>\n";
        }
        $num1++;
        if($more_or_less eq "less" ) { 
           if($num1==15) {last;}
        }
    } 
   print"<tr><td></td><td>Total</td><td>$total</td></tr>\n";
   print "</table>";
    if ($more_or_less eq "less" ) {
    print "<input type='button' id='button_value' value='more' form='myform' onclick=my_function()>";
    }else {
    print "<input type='button' id='button_value' value='less' form='myform' onclick=my_function()>";
    } 
print"</td><td>&nbsp&nbsp</td>\n";
print"<td>";
  print "<table  style='border-collapse:collapse;width:20%' class='simple_table'>\n";
  print "<tr><th>S.no</th><th>Failure Reason</th>\n";
  #print"<th>#Testcases</th>\n";
  print"<th>#Testcases<br>(NO CCR)</th>\n";
  print"<th>#Testcases<br>(CCR)</th>\n";
  print"</tr>\n";
  $num1=1;
  for($i=0;$i<=$#all_reasons;$i++) {
        $reason=$all_reasons[$i];
        $reason1=$all_reasons1[$i];
        print"<tr><td>$num1</td><td>$reason1</td>\n";
	#print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket&reason=$reason' target='_blank'>$reason_count{$reason}</a></td>\n";
	print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket&reason=$reason&ccr=no' target='_blank'>$reason_count_noccr{$reason}</a></td>\n";
	print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket&reason=$reason&ccr=yes' target='_blank'>$reason_count_ccr{$reason}</a></td>\n";
	print"</tr>\n";
        $num1++;
  } 
        print"<tr><td></td><td><b>ALL FAILURES</b></td>\n";
	#print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket' target='_blank'>$reason_count{'all_failures'} (unique)</a></td>\n";
	print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket&ccr=no' target='_blank'>$reason_count{'all_failures_noccr'} (unique)</a></td>\n";
	print"<td><a href='http://etpv/cgi-bin/gcov_failure_reasons/list_matching_criteria.pl?build=$build&bucket=$bucket&ccr=yes' target='_blank'>$reason_count{'all_failures_ccr'} (unique)</a></td>\n";
	print"</tr>";
  print "</table>";
print"</td>";
print"</tr></table>";
print "<table id='example' style='width:80%;margin:0 auto;' border='1' bordercolor='BLACK'  class='w3-table-all'>\n";

print "<thead><tr class='w3-yellow'>";
print "<th>S.no</th><th style='word-wrap:break-word;max-width:1200px;'>Testcase Path</th><th>Reason</th><th style='word-wrap:break-word;max-width:300px;'>Command</th><th style='word-wrap:break-word;max-width:200px;'>CCR</th>";
print "</tr>\n";
#print"<tr style='border: 1px solid black;'><th></th><th></th><th>SELECT</th><th>SELECT</th></tr>";
print"</thead>";
print "<tbody>";
my $num=1;
for($i=0 ; $i<=$#data ; $i++) {
    #print "$data[$i]<br>";
    my @actuals = split("::::",$data[$i]);
    print "<tr><td>$num</td><td style='word-wrap:break-word;max-width:1200px;'><a href='$actuals[0]' target='_blank'>$actuals[0]</a></td>\n";
    if ( $actuals[1] =~ m/^E\s+\S+\s+\S+$/) {
         ($msgid = $actuals[1] ) =~ s/^E\s+(\S+)\s+\S+$/$1/g ;
         ($others = $actuals[1] ) =~ s/^E\s+\S+\s+(\S+)$/$1/g;
         print"<td><pre>E <a href='http://etpv/cgi-bin/msgid_analysis/msginfo?msgid=$msgid' target='_blank' >$msgid</a> $others</pre></td>\n";
     }
     else {
       print"<td><pre>$actuals[1]</pre></td>\n";
      }
    print"<td style='word-wrap:break-word;max-width:300px;'><pre>$actuals[2]</pre></td>\n";
    if($actuals[3] =~ m/^(CCR|CCMPR)*\d+$/) {
       print"<td><a  href='http://ccmsutil/cgi-bin/ccrprint.cgi?ccrId=$actuals[3]' target='_blank' >$actuals[3]</a></td></tr>";
     } 
    else {
       print"<td>$actuals[3]</td></tr>";
    }
    $num++;
}
print"</tbody>";
print "</table>";

print "</body>";
print <<END;
<script language='javascript'>
   function my_function() {
        var more_or_less = document.getElementById("button_value").value;
        document.getElementById("more_or_less").value = more_or_less;
        document.getElementById("myform").submit();
   }
     function my_function2() {
     var bucket_or_owner = document.getElementById("button_value1").value;
     document.getElementById("bucket_or_owner").value = bucket_or_owner;
     document.getElementById("myform").submit();
   }


</script>
END
print "</html>"; 
