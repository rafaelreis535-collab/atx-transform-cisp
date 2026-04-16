      ******************************************************************
      * DCLGEN TABLE(BANKING.BANK_CONTROL)                             *
      *        LIBRARY(BANKPRD.GE.A.DCLGEN(BKCONTRL))                  *
      *        ACTION(REPLACE)                                         *
      *        LANGUAGE(COBOL)                                         *
      *        NAMES(BKCONTRL-)                                        *
      *        QUOTE                                                   *
      *        COLSUFFIX(YES)                                          *
      * ... IS THE DCLGEN COMMAND THAT MADE THE FOLLOWING STATEMENTS   *
      ******************************************************************
           EXEC SQL DECLARE BANKING.BANK_CONTROL TABLE
           ( SYSTEM_ID                     CHAR(2) NOT NULL,
             PROC_DATE                     DATE NOT NULL,
             LAST_CLOSE_DATE               DATE NOT NULL,
             STATUS                        CHAR(1) NOT NULL,
             USER_CODE                     CHAR(8) NOT NULL,
             TIMESTAMP                     TIMESTAMP NOT NULL
           ) END-EXEC.
      ******************************************************************
      * COBOL DECLARATION FOR TABLE BANKING.BANK_CONTROL               *
      ******************************************************************
       01  DCLBANK-CONTROL.
      *                       SYSTEM_ID
           10 BKCONTRL-SYSTEM-ID
              PIC X(2).
      *                       PROC_DATE
           10 BKCONTRL-PROC-DATE
              PIC X(10).
      *                       LAST_CLOSE_DATE
           10 BKCONTRL-LAST-CLOSE-DATE
              PIC X(10).
      *                       STATUS
           10 BKCONTRL-STATUS
              PIC X(1).
      *                       USER_CODE
           10 BKCONTRL-USER-CODE
              PIC X(8).
      *                       TIMESTAMP
           10 BKCONTRL-TIMESTAMP
              PIC X(26).
      ******************************************************************
      * THE NUMBER OF COLUMNS DESCRIBED BY THIS DECLARATION IS 6       *
      ******************************************************************