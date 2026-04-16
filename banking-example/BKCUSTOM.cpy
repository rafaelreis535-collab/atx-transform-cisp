      ******************************************************************
      * DCLGEN TABLE(BANKING.CUSTOMERS)                                *
      *        LIBRARY(BANKPRD.GE.A.DCLGEN(BKCUSTOM))                  *
      *        ACTION(REPLACE)                                         *
      *        LANGUAGE(COBOL)                                         *
      *        NAMES(BKCUSTOM-)                                        *
      *        QUOTE                                                   *
      *        COLSUFFIX(YES)                                          *
      * ... IS THE DCLGEN COMMAND THAT MADE THE FOLLOWING STATEMENTS   *
      ******************************************************************
           EXEC SQL DECLARE BANKING.CUSTOMERS TABLE
           ( CUSTOMER_ID                   INTEGER NOT NULL,
             CUSTOMER_NAME                 CHAR(40) NOT NULL,
             CUSTOMER_TYPE                 CHAR(1) NOT NULL,
             TAX_ID                        CHAR(14) NOT NULL,
             DATE_OF_BIRTH                 DATE,
             EMAIL                         CHAR(50),
             PHONE_NUMBER                  CHAR(15),
             STATUS                        CHAR(1) NOT NULL,
             REGISTRATION_DATE             DATE NOT NULL,
             USER_CODE                     CHAR(8) NOT NULL,
             TIMESTAMP                     TIMESTAMP NOT NULL
           ) END-EXEC.
      ******************************************************************
      * COBOL DECLARATION FOR TABLE BANKING.CUSTOMERS                  *
      ******************************************************************
       01  DCLCUSTOMERS.
      *                       CUSTOMER_ID
           10 BKCUSTOM-CUSTOMER-ID
              PIC S9(9) USAGE COMP.
      *                       CUSTOMER_NAME
           10 BKCUSTOM-CUSTOMER-NAME
              PIC X(40).
      *                       CUSTOMER_TYPE
           10 BKCUSTOM-CUSTOMER-TYPE
              PIC X(1).
      *                       TAX_ID
           10 BKCUSTOM-TAX-ID
              PIC X(14).
      *                       DATE_OF_BIRTH
           10 BKCUSTOM-DATE-OF-BIRTH
              PIC X(10).
      *                       EMAIL
           10 BKCUSTOM-EMAIL
              PIC X(50).
      *                       PHONE_NUMBER
           10 BKCUSTOM-PHONE-NUMBER
              PIC X(15).
      *                       STATUS
           10 BKCUSTOM-STATUS
              PIC X(1).
      *                       REGISTRATION_DATE
           10 BKCUSTOM-REGISTRATION-DATE
              PIC X(10).
      *                       USER_CODE
           10 BKCUSTOM-USER-CODE
              PIC X(8).
      *                       TIMESTAMP
           10 BKCUSTOM-TIMESTAMP
              PIC X(26).
      ******************************************************************
      * THE NUMBER OF COLUMNS DESCRIBED BY THIS DECLARATION IS 11      *
      ******************************************************************