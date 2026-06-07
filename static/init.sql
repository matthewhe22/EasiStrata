
alter table trust_adj alter is_valid set default True;
alter table trust_adj alter is_adjust set default True;


alter table base_TB alter ownership set default 1.0000;


alter table trust_taxinput alter original_amount set default 0.00;
alter table trust_taxinput alter adj_amount set default 0.00;


alter table base_clientaccountdetails alter is_valid set default True;
alter table trust_tbmap alter is_valid set default True;


alter table trust_trustownership alter ownership set default 1.0000;

alter table trust_falist alter ownership set default 1.0000;