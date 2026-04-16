      ******************************************************************
      * DCLGEN TABLE(BANKING.TRANSACTIONS)                             *
      *        LIBRARY(BANKPRD.GE.A.DCLGEN(BKTRANSC))                  *
      *        ACTION(REPLACE)                                         *
      *        LANGUAGE(COBOL)                                         *
      *        NAMES(BKTRANSC-)                                        *
      *        QUOTE                                                   *
      *        COLSUFFIX(YES)                                          *
      * ... IS THE DCLGEN COMMAND THAT MADE THE FOLLOWING STATEMENTS   *
      ******************************************************************
           EXEC SQL DECLARE BANKING.TRANSACTIONS TABLE
           ( TRANSACTION_ID                INTEGER NOT NULL,
             ACCOUNT_NUMBER               CHAR(10) NOT NULL,
             TRANSACTION_TYPE             CHAR(2) NOT NULL,
             TRANSACTION_DATE             DATE NOT NULL,
             TRANSACTION_AMOUNT           DECIMAL(15,2) NOT NULL,
             BALANCE_AFTER                DECIMAL(15,2) NOT NULL,
             DESCRIPTION                  CHAR(50) NOT NULL,
             STATUS                       CHAR(1) NOT NULL,
             CHANNEL                      CHAR(3) NOT NULL,
             USER_CODE                    CHAR(8) NOT NULL,
             TIMESTAMP                    TIMESTAMP NOT NULL
           ) END-EXEC.
      ******************************************************************
      * COBOL DECLARATION FOR TABLE BANKING.TRANSACTIONS               *
      ******************************************************************
       01  DCLTRANSACTIONS.
      *                       TRANSACTION_ID
           10 BKTRANSC-TRANSACTION-ID
              PIC S9(9) USAGE COMP.
      *                       ACCOUNT_NUMBER
           10 BKTRANSC-ACCOUNT-NUMBER
              PIC X(10).
      *                       TRANSACTION_TYPE
           10 BKTRANSC-TRANSACTION-TYPE
              PIC X(2).
      *                       TRANSACTION_DATE
           10 BKTRANSC-TRANSACTION-DATE
              PIC X(10).
      *                       TRANSACTION_AMOUNT
           10 BKTRANSC-TRANSACTION-AMOUNT
              PIC S9(13)V99 USAGE COMP-3.
      *                       BALANCE_AFTER
           10 BKTRANSC-BALANCE-AFTER
              PIC S9(13)V99 USAGE COMP-3.
      *                       DESCRIPTION
           10 BKTRANSC-DESCRIPTION
              PIC X(50).
      *                       STATUS
           10 BKTRANSC-STATUS
              PIC X(1).
      *                       CHANNEL
           10 BKTRANSC-CHANNEL
              PIC X(3).
      *                       USER_CODE
           10 BKTRANSC-USER-CODE
              PIC X(8).
      *                       TIMESTAMP
           10 BKTRANSC-TIMESTAMP
              PIC X(26).
      ******************************************************************
      * THE NUMBER OF COLUMNS DESCRIBED BY THIS DECLARATION IS 11      *
      ******************************************************************