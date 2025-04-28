import {CheckCircleIcon, CopyIcon} from "lucide-react";
import React, {JSX} from "react";
import styles from "./DivByAnima.module.css";

export const DivByAnima = (): JSX.Element => {
  const userData = {
    name: "Кристина Соколова",
    welcomeMessage: "С возвращением!",
    profileImage: "/profile/rectangle-12960.png",
    uid: "9999999999",
    verificationType: "Верифицирован",
    userType: "Личный",
    vipLevel: "Нету",
    email: "kristina_sokolova@mail.ru",
    referralLink: "https://сrypto.com/referral/USERNAME",
  };

  const accounts = [
    {
      type: "Лицевой счет",
      balance: "170.43 USDT",
      iconSrc: "/profile/vector-12.svg",
      actions: ["Пополнить", "Вывести", "Инвестировать"],
    },
    {
      type: "Партнерский счет",
      balance: "**** USDT",
      iconSrc: "/profile/vector-10.svg",
      actions: ["Пополнить", "Вывести"],
    },
  ];

  return (
    <div className={styles.container}>
      {/* Profile Section */}
      <div className={styles.profileSection}>
        <div className={styles.profilePicture}>
          <img
            className={styles.profileImage}
            alt="Profile"
            src={userData.profileImage}
          />
        </div>

        <div className={styles.userInfo}>
          <p className={styles.welcomeMessage}>{userData.welcomeMessage}</p>
          <div className={styles.nameContainer}>
            <h2 className={styles.userName}>{userData.name}</h2>
            <img className={styles.editIcon} alt="Edit" src="/profile/edit-2.png"/>
          </div>
        </div>
      </div>

      {/* Cards Grid */}
      <div className={styles.cardsGrid}>
        {/* User Info Cards */}
        <div className={styles.cardUserWrapp}>
          <div className={styles.card}>
            <div className={styles.cardContent}>
              <div>
                <p className={styles.cardLabel}>UID</p>
                <p className={styles.cardValue}>{userData.uid}</p>
              </div>
              <CopyIcon className={styles.icon}/>
            </div>
          </div>

          <div className={styles.card}>
            <div className={styles.cardContent}>
              <div>
                <p className={styles.cardLabel}>Тип пользователя</p>
                <p className={styles.cardValue}>{userData.userType}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Verification & VIP */}
        <div className={styles.cardUserWrapp}>
          <div className={styles.card}>
            <div className={styles.cardContent}>
              <div>
                <p className={styles.cardLabel}>Проверка личности</p>
                <p className={styles.cardValue}>{userData.verificationType}</p>
              </div>
              <CheckCircleIcon className={styles.icon}/>
            </div>
          </div>

          <div className={styles.card}>
            <div className={styles.cardContent}>
              <div>
                <p className={styles.cardLabel}>VIP уровень</p>
                <p className={styles.cardValue}>{userData.vipLevel}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Accounts */}
        {accounts.map((account, idx) => (
          <div key={idx} className={styles.cardUserWrapp}>
            <div key={idx} className={styles.card}>
              <div className={styles.accountCard}>
                <div className={styles.accountBalanceWrap}>
                  <div className={styles.accountType}>
                    <p className={styles.accountTypeText}>{account.type}</p>
                    <img src={account.iconSrc} alt="Account Icon"/>
                  </div>
                  <p className={styles.accountBalance}>{account.balance}</p>
                </div>
                <div className={styles.accountActions}>
                  {account.actions.map((action, actionIdx) => (
                    <button
                      key={actionIdx}
                      className={`${styles.actionButton} ${actionIdx === 1 ? styles.actionButtonOutline : ""}`}
                    >
                      {action}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            {idx == 0 && <div className={styles.card}>
              <div className={styles.cardContent}>
                <p className={styles.cardLabel}>Почта</p>
                <p className={styles.cardValue}>{userData.email}</p>
              </div>
            </div>}

            {idx == 1 && <div className={styles.card}>
              <div className={styles.cardContent}>
                <div>
                  <p className={styles.cardLabel}>Реферальная ссылка</p>
                  <p className={styles.cardValue}>{userData.referralLink}</p>
                </div>
                <CopyIcon className={styles.icon}/>
              </div>
            </div>}
          </div>

        ))}
      </div>

      {/* Bottom Row */}
      {/*<div className={styles.bottomRow}>*/}
      {/*  <div className={styles.card}>*/}
      {/*    <div className={styles.cardContent}>*/}
      {/*      <p className={styles.cardLabel}>Почта</p>*/}
      {/*      <p className={styles.cardValue}>{userData.email}</p>*/}
      {/*    </div>*/}
      {/*  </div>*/}

      {/*  <div className={styles.card}>*/}
      {/*    <div className={styles.cardContent}>*/}
      {/*      <div>*/}
      {/*        <p className={styles.cardLabel}>Реферальная ссылка</p>*/}
      {/*        <p className={styles.cardValue}>{userData.referralLink}</p>*/}
      {/*      </div>*/}
      {/*      <CopyIcon className={styles.icon}/>*/}
      {/*    </div>*/}
      {/*  </div>*/}
      {/*</div>*/}
    </div>
  );
};