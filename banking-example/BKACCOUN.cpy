      ******************************************************************
      * DCLGEN TABLE(BANKING.ACCOUNTS)                                 *
      *        LIBRARY(BANKPRD.GE.A.DCLGEN(BKACCOUN))                  *
      *        ACTION(REPLACE)                                         *
      *        LANGUAGE(COBOL)                                         *
      *        NAMES(BKACCOUN-)                                        *
      *        QUOTE                                                   *
      *        COLSUFFIX(YES)                                          *
      * ... IS THE DCLGEN COMMAND THAT MADE THE FOLLOWING STATEMENTS   *
      ******************************************************************
           EXEC SQL DECLARE BANKING.ACCOUNTS TABLE
           ( ACCOUNT_NUMBER                CHAR(10) NOT NULL,
             CUSTOMER_ID                   INTEGER NOT NULL,
             ACCOUNT_TYPE                  CHAR(2) NOT NULL,
             ACCOUNT_STATUS                CHAR(1) NOT NULL,
             BALANCE                       DECIMAL(15,2) NOT NULL,
             CREDIT_LIMIT                  DECIMAL(15,2) NOT NULL,
             OPEN_DATE                     DATE NOT NULL,
             LAST_MOVEMENT_DATE            DATE,
             BRANCH_CODE                   SMALLINT NOT NULL,
             CURRENCY_CODE                 CHAR(3) NOT NULL,
             USER_CODE                     CHAR(8) NOT NULL,
             TIMESTAMP                     TIMESTAMP NOT NULL
           ) END-EXEC.
      ******************************************************************
      * COBOL DECLARATION FOR TABLE BANKING.ACCOUNTS                   *
      ******************************************************************
       01  DCLACCOUNTS.
      *                       ACCOUNT_NUMBER
           10 BKACCOUN-ACCOUNT-NUMBER
              PIC X(10).
      *                       CUSTOMER_ID
           10 BKACCOUN-CUSTOMER-ID
              PIC S9(9) USAGE COMP.
      *                       ACCOUNT_TYPE
           10 BKACCOUN-ACCOUNT-TYPE
              PIC X(2).
      *                       ACCOUNT_STATUS
           10 BKACCOUN-ACCOUNT-STATUS
              PIC X(1).
      *                       BALANCE
           10 BKACCOUN-BALANCE
              PIC S9(13)V99 USAGE COMP-3.
      *                       CREDIT_LIMIT
           10 BKACCOUN-CREDIT-LIMIT
              PIC S9(13)V99 USAGE COMP-3.
      *                       OPEN_DATE
           10 BKACCOUN-OPEN-DATE
              PIC X(10).
      *                       LAST_MOVEMENT_DATE
           10 BKACCOUN-LAST-MOVEMENT-DATE
              PIC X(10).
      *                       BRANCH_CODE
           10 BKACCOUN-BRANCH-CODE
              PIC S9(4) USAGE COMP.
      *                       CURRENCY_CODE
           10 BKACCOUN-CURRENCY-CODE
              PIC X(3).
      *                       USER_CODE
           10 BKACCOUN-USER-CODE
              PIC X(8).
      *                       TIMESTAMP
           10 BKACCOUN-TIMESTAMP
              PIC X(26).
      ******************************************************************
      * THE NUMBER OF COLUMNS DESCRIBED BY THIS DECLARATION IS 12      *
      ******************************************************************