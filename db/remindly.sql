-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Sep 06, 2025 at 08:05 AM
-- Server version: 10.4.25-MariaDB
-- PHP Version: 8.1.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `remindly`
--
CREATE DATABASE IF NOT EXISTS `remindly` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `remindly`;

-- --------------------------------------------------------

--
-- Table structure for table `reminders`
--

CREATE TABLE `reminders` (
  `reminder_id` bigint(20) NOT NULL,
  `reminder_uuid` varchar(255) NOT NULL,
  `reminder_url_slug` varchar(255) NOT NULL,
  `reminder_title` varchar(255) NOT NULL,
  `reminder_desc` varchar(1000) DEFAULT NULL,
  `reminder_link` varchar(1000) DEFAULT NULL,
  `reminder_type` varchar(255) NOT NULL,
  `reminder_recurrence_type` varchar(20) NOT NULL DEFAULT 'NONE',
  `reminder_recurrence_rrule` varchar(1000) DEFAULT NULL,
  `reminder_date_start` date DEFAULT NULL,
  `reminder_date_end` date DEFAULT NULL,
  `reminder_is_completed` tinyint(1) NOT NULL DEFAULT 0,
  `reminder_user_uuid` varchar(255) NOT NULL,
  `created_on` datetime NOT NULL,
  `updated_on` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `shared_reminders`
--

CREATE TABLE `shared_reminders` (
  `shared_reminder_id` bigint(20) NOT NULL,
  `shared_reminder_uuid` varchar(255) NOT NULL,
  `shared_reminder_reminder_uuid` varchar(255) NOT NULL,
  `shared_reminder_user_uuid` varchar(255) NOT NULL,
  `created_on` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_on` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` bigint(20) NOT NULL,
  `user_uuid` varchar(255) NOT NULL,
  `user_username` varchar(255) NOT NULL,
  `user_password` varchar(255) NOT NULL,
  `user_email` varchar(255) NOT NULL,
  `user_alert_webhook_url` varchar(500) DEFAULT NULL,
  `created_on` datetime NOT NULL,
  `updated_on` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `reminders`
--
ALTER TABLE `reminders`
  ADD PRIMARY KEY (`reminder_id`),
  ADD UNIQUE KEY `reminder_uuid` (`reminder_uuid`),
  ADD UNIQUE KEY `reminder_url_slug` (`reminder_url_slug`),
  ADD KEY `reminder_user_uuid` (`reminder_user_uuid`) USING BTREE;

--
-- Indexes for table `shared_reminders`
--
ALTER TABLE `shared_reminders`
  ADD PRIMARY KEY (`shared_reminder_id`),
  ADD UNIQUE KEY `shared_reminder_uuid` (`shared_reminder_uuid`) USING BTREE,
  ADD KEY `shared_reminder_user_uuid_idx` (`shared_reminder_user_uuid`) USING BTREE,
  ADD KEY `shared_reminder_reminder_uuid_idx` (`shared_reminder_reminder_uuid`) USING BTREE;

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `user_uuid` (`user_uuid`) USING BTREE;

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `reminders`
--
ALTER TABLE `reminders`
  MODIFY `reminder_id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `shared_reminders`
--
ALTER TABLE `shared_reminders`
  MODIFY `shared_reminder_id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` bigint(20) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
